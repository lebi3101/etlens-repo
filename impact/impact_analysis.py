import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import networkx as nx
from dotenv import load_dotenv

load_dotenv()


def build_dependency_graph(all_parsed: list) -> nx.DiGraph:
    """
    Builds a directed graph where:
    - Nodes = scripts, tables, and files
    - Edges = data flow (source -> script -> target)

    Args:
        all_parsed: List of parsed dicts from python/sql parsers

    Returns:
        A NetworkX directed graph
    """
    G = nx.DiGraph()

    for parsed in all_parsed:
        script_name = parsed.get("file", "unknown")
        sources = parsed.get("sources", [])
        targets = parsed.get("targets", [])

        # Add the script as a node
        G.add_node(script_name, node_type="script")

        # Add source nodes and edges: source -> script
        for source in sources:
            G.add_node(source, node_type="source")
            G.add_edge(source, script_name, relationship="feeds_into")

        # Add target nodes and edges: script -> target
        for target in targets:
            G.add_node(target, node_type="target")
            G.add_edge(script_name, target, relationship="writes_to")

    return G


def get_impact_analysis(script_name: str, G: nx.DiGraph) -> dict:
    """
    Analyzes what is affected if a given script fails or changes.

    Args:
        script_name: The ETL script filename to analyze
        G: The dependency graph

    Returns:
        Dict with full impact report
    """
    if script_name not in G:
        return {"error": f"Script '{script_name}' not found in dependency graph."}

    # Direct upstream: what feeds INTO this script
    upstream = list(G.predecessors(script_name))

    # Direct downstream: what this script writes to
    direct_outputs = list(G.successors(script_name))

    # All downstream (transitive): everything affected down the chain
    all_downstream = list(nx.descendants(G, script_name))

    # All upstream (transitive): everything this depends on
    all_upstream = list(nx.ancestors(G, script_name))

    # Scripts (not tables) that depend on this script's outputs
    affected_scripts = [
        node for node in all_downstream
        if G.nodes[node].get("node_type") == "script"
    ]

    # Determine risk level
    if len(all_downstream) == 0:
        risk_level = "LOW"
        risk_reason = "This script has no downstream dependencies."
    elif len(affected_scripts) == 0:
        risk_level = "MEDIUM"
        risk_reason = f"Failure affects {len(direct_outputs)} output(s) but no other scripts directly."
    else:
        risk_level = "HIGH"
        risk_reason = f"Failure affects {len(affected_scripts)} other script(s) and {len(direct_outputs)} output(s)."

    return {
        "script": script_name,
        "risk_level": risk_level,
        "risk_reason": risk_reason,
        "upstream_dependencies": upstream,
        "all_upstream": all_upstream,
        "direct_outputs": direct_outputs,
        "all_downstream": all_downstream,
        "affected_scripts": affected_scripts,
        "total_nodes_affected": len(all_downstream)
    }


def analyze_all_scripts(all_parsed: list) -> dict:
    """
    Runs impact analysis for every script in the parsed list.

    Returns:
        Dict mapping filename -> impact report
    """
    G = build_dependency_graph(all_parsed)
    results = {}
    for parsed in all_parsed:
        script_name = parsed.get("file", "unknown")
        results[script_name] = get_impact_analysis(script_name, G)
    return results, G


def print_impact_report(impact: dict):
    """Pretty prints an impact report."""
    print(f"\n  Script     : {impact.get('script')}")
    print(f"  Risk Level : {impact.get('risk_level')}")
    print(f"  Reason     : {impact.get('risk_reason')}")
    print(f"  Depends on : {impact.get('upstream_dependencies') or 'Nothing'}")
    print(f"  Writes to  : {impact.get('direct_outputs') or 'Nothing'}")
    print(f"  Affected scripts if this fails: {impact.get('affected_scripts') or 'None'}")
    print(f"  Total nodes affected: {impact.get('total_nodes_affected')}")


if __name__ == "__main__":
    from parser.python_parser import parse_python_etl
    from parser.sql_parser import parse_sql_etl

    print("Testing Impact Analysis...\n")

    parsed_orders = parse_python_etl("etl_samples/sample_orders.py")
    parsed_hr = parse_python_etl("etl_samples/sample_hr.py")
    parsed_sales = parse_sql_etl("etl_samples/sample_sales.sql")

    all_parsed = [parsed_orders, parsed_hr, parsed_sales]

    results, G = analyze_all_scripts(all_parsed)

    print(f"Dependency graph has {G.number_of_nodes()} nodes and {G.number_of_edges()} edges\n")
    print("=" * 60)

    for script_name, impact in results.items():
        print(f"\nImpact report for: {script_name}")
        print("-" * 40)
        print_impact_report(impact)

    print("\n✅ Impact analysis test complete!")