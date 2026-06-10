import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.llm_client import query_llm

SYSTEM_PROMPT = """You are a business analyst who explains technical ETL pipelines 
to non-technical business stakeholders. Focus on business value, not technical details.
Be concise and use plain language."""


def explain_business_purpose(parsed_data: dict) -> str:
    """
    Explains the business reason this ETL script exists.

    Args:
        parsed_data: dict from python_parser or sql_parser

    Returns:
        A plain English business explanation string
    """
    file_name = parsed_data.get("file", "unknown")
    sources = parsed_data.get("sources", [])
    targets = parsed_data.get("targets", [])
    transformations = parsed_data.get("transformations", [])

    prompt = f"""ETL script '{file_name}' reads {', '.join(sources[:2]) if sources else 'unknown'} and writes to {', '.join(targets[:2]) if targets else 'unknown'}.

Answer in 2 sentences each:
1. Business Purpose:
2. Who Benefits:
3. Risk if Fails:"""

    return query_llm(prompt, system_prompt=SYSTEM_PROMPT)


def explain_all(all_parsed: list) -> dict:
    """
    Generates business explanations for a list of parsed ETL scripts.

    Args:
        all_parsed: List of parsed dicts

    Returns:
        Dict mapping filename -> business explanation string
    """
    results = {}
    for parsed in all_parsed:
        file_name = parsed.get("file", "unknown")
        print(f"  Explaining business purpose for: {file_name}...")
        results[file_name] = explain_business_purpose(parsed)
    return results


if __name__ == "__main__":
    from parser.python_parser import parse_python_etl
    from parser.sql_parser import parse_sql_etl

    print("Testing Business Purpose Explainer...\n")
    print("=" * 60)

    parsed_orders = parse_python_etl("etl_samples/sample_orders.py")
    parsed_hr = parse_python_etl("etl_samples/sample_hr.py")
    parsed_sales = parse_sql_etl("etl_samples/sample_sales.sql")

    all_parsed = [parsed_orders, parsed_hr, parsed_sales]
    explanations = explain_all(all_parsed)

    for filename, explanation in explanations.items():
        print(f"\n{'=' * 60}")
        print(f"FILE: {filename}")
        print(explanation)

    print("\n✅ Business explainer test complete!")