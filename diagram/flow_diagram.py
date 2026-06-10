import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from graphviz import Digraph
from dotenv import load_dotenv

load_dotenv()

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
DIAGRAMS_DIR = os.path.join(OUTPUT_DIR, "diagrams")
os.makedirs(DIAGRAMS_DIR, exist_ok=True)


def generate_flow_diagram(parsed_data: dict) -> str:
    """
    Generates a Graphviz flow diagram for an ETL script.

    Args:
        parsed_data: dict from python_parser or sql_parser

    Returns:
        File path of the saved diagram (PNG)
    """
    file_name = parsed_data.get("file", "unknown")
    sources = parsed_data.get("sources", [])
    targets = parsed_data.get("targets", [])
    transformations = parsed_data.get("transformations", [])

    # Create a new directed graph
    dot = Digraph(
        name=file_name,
        format="png",
        graph_attr={
            "rankdir": "LR",        # Left to Right flow
            "splines": "ortho",
            "bgcolor": "white",
            "pad": "0.5"
        }
    )

    # --- SOURCE nodes (blue) ---
    with dot.subgraph(name="cluster_sources") as s:
        s.attr(label="Sources", style="filled", color="lightblue", fontsize="12")
        if sources:
            for source in sources:
                s.node(
                    f"src_{source}",
                    label=source,
                    shape="cylinder",
                    style="filled",
                    fillcolor="#4A90D9",
                    fontcolor="white",
                    fontsize="10"
                )
        else:
            s.node("src_unknown", label="Unknown Source",
                   shape="cylinder", style="filled",
                   fillcolor="#4A90D9", fontcolor="white")

    # --- TRANSFORMATION nodes (orange) ---
    with dot.subgraph(name="cluster_transforms") as t:
        t.attr(label="Transformations", style="filled",
               color="lightyellow", fontsize="12")
        if transformations:
            for i, transform in enumerate(transformations):
                t.node(
                    f"tr_{i}",
                    label=transform,
                    shape="rectangle",
                    style="filled,rounded",
                    fillcolor="#F5A623",
                    fontcolor="white",
                    fontsize="10"
                )
        else:
            t.node("tr_none", label="No Transformations",
                   shape="rectangle", style="filled,rounded",
                   fillcolor="#F5A623", fontcolor="white")

    # --- TARGET nodes (green) ---
    with dot.subgraph(name="cluster_targets") as tg:
        tg.attr(label="Targets", style="filled",
                color="lightgreen", fontsize="12")
        if targets:
            for target in targets:
                tg.node(
                    f"tgt_{target}",
                    label=target,
                    shape="cylinder",
                    style="filled",
                    fillcolor="#7ED321",
                    fontcolor="white",
                    fontsize="10"
                )
        else:
            tg.node("tgt_unknown", label="Unknown Target",
                    shape="cylinder", style="filled",
                    fillcolor="#7ED321", fontcolor="white")

    # --- EDGES: Sources → first transformation ---
    first_transform = f"tr_0" if transformations else "tr_none"
    source_nodes = [f"src_{s}" for s in sources] if sources else ["src_unknown"]

    for src_node in source_nodes:
        dot.edge(src_node, first_transform, color="#4A90D9", penwidth="2")

    # --- EDGES: transformations chain ---
    for i in range(len(transformations) - 1):
        dot.edge(f"tr_{i}", f"tr_{i+1}", color="#F5A623", penwidth="2")

    # --- EDGES: last transformation → targets ---
    last_transform = f"tr_{len(transformations)-1}" if transformations else "tr_none"
    target_nodes = [f"tgt_{t}" for t in targets] if targets else ["tgt_unknown"]

    for tgt_node in target_nodes:
        dot.edge(last_transform, tgt_node, color="#7ED321", penwidth="2")

    # --- Save diagram ---
    base_name = file_name.replace(".", "_")
    output_path = os.path.join(DIAGRAMS_DIR, base_name)
    dot.render(output_path, cleanup=True)

    final_path = output_path + ".png"
    print(f"  Diagram saved: {final_path}")
    return final_path


def generate_all_diagrams(all_parsed: list) -> dict:
    """
    Generates diagrams for all parsed ETL scripts.

    Returns:
        Dict mapping filename -> diagram path
    """
    results = {}
    for parsed in all_parsed:
        file_name = parsed.get("file", "unknown")
        print(f"  Generating diagram for: {file_name}...")
        results[file_name] = generate_flow_diagram(parsed)
    return results


if __name__ == "__main__":
    from parser.python_parser import parse_python_etl
    from parser.sql_parser import parse_sql_etl

    print("Testing Flow Diagram Generator...\n")

    parsed_orders = parse_python_etl("etl_samples/sample_orders.py")
    parsed_hr = parse_python_etl("etl_samples/sample_hr.py")
    parsed_sales = parse_sql_etl("etl_samples/sample_sales.sql")

    all_parsed = [parsed_orders, parsed_hr, parsed_sales]
    diagrams = generate_all_diagrams(all_parsed)

    print("\nGenerated diagrams:")
    for filename, path in diagrams.items():
        print(f"  {filename} -> {path}")

    print("\n✅ Flow diagram test complete!")