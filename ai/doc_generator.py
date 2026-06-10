import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai.llm_client import query_llm

SYSTEM_PROMPT = """You are a technical documentation expert for ETL pipelines.
Write clear, concise documentation for developers and business users."""


def generate_documentation(parsed_data: dict) -> str:
    file_name = parsed_data.get("file", "unknown")
    script_type = parsed_data.get("type", "unknown")
    sources = parsed_data.get("sources", [])
    targets = parsed_data.get("targets", [])
    transformations = parsed_data.get("transformations", [])

    prompt = f"""Document this ETL script in 3 short sections:

File: {file_name} | Type: {script_type}
Sources: {', '.join(sources[:3]) if sources else 'N/A'}
Targets: {', '.join(targets[:3]) if targets else 'N/A'}
Transforms: {', '.join(list(transformations)[:4]) if transformations else 'N/A'}

Write:
**Overview** (1 sentence)
**What It Does** (2 bullet points)
**Output** (1 sentence)"""

    return query_llm(prompt, system_prompt=SYSTEM_PROMPT)


def generate_docs_for_folder(all_parsed: list) -> dict:
    results = {}
    for parsed in all_parsed:
        file_name = parsed.get("file", "unknown")
        print(f"  Generating docs for: {file_name}...")
        results[file_name] = generate_documentation(parsed)
    return results


if __name__ == "__main__":
    from parser.python_parser import parse_python_etl
    from parser.sql_parser import parse_sql_etl

    print("Testing Documentation Generator...\n")
    print("=" * 60)

    parsed_orders = parse_python_etl("etl_samples/sample_orders.py")
    parsed_hr = parse_python_etl("etl_samples/sample_hr.py")
    parsed_sales = parse_sql_etl("etl_samples/sample_sales.sql")

    all_parsed = [parsed_orders, parsed_hr, parsed_sales]
    docs = generate_docs_for_folder(all_parsed)

    for filename, doc in docs.items():
        print(f"\n{'=' * 60}")
        print(f"FILE: {filename}")
        print(doc)

    print("\n✅ Documentation generator test complete!")