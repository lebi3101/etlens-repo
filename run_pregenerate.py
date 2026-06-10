import sys, os
sys.path.insert(0, '.')
import json

from parser.python_parser import parse_python_etl
from parser.sql_parser import parse_sql_etl
from ai.doc_generator import generate_documentation
from ai.business_explainer import explain_business_purpose
from diagram.flow_diagram import generate_flow_diagram
from impact.impact_analysis import analyze_all_scripts
from ai.rag_pipeline import RAGPipeline

CACHE_FILE = "output/pregenerated_cache.json"
os.makedirs("output", exist_ok=True)

print("=" * 60)
print("PRE-GENERATING ALL OUTPUTS FOR DEMO")
print("Run this ONCE before your presentation")
print("=" * 60)

# Step 1: Parse
print("\n[1/5] Parsing all sample scripts...")
parsed_orders = parse_python_etl("etl_samples/sample_orders.py")
parsed_hr = parse_python_etl("etl_samples/sample_hr.py")
parsed_sales = parse_sql_etl("etl_samples/sample_sales.sql")
all_parsed = [parsed_orders, parsed_hr, parsed_sales]
print("✅ Parsing done")

# Step 2: Generate documentation
print("\n[2/5] Generating documentation (this takes time)...")
docs = {}
for parsed in all_parsed:
    fname = parsed["file"]
    print(f"  Generating doc for {fname}...")
    doc = generate_documentation(parsed)
    if "ERROR" in doc:
        doc = f"**Overview**\nThis script reads from {', '.join(parsed.get('sources', []))} and writes to {', '.join(parsed.get('targets', []))}.\n\n**What It Does**\n- Sources: {', '.join(parsed.get('sources', []))}\n- Transformations: {', '.join(parsed.get('transformations', []))}\n\n**Output**\nWrites to: {', '.join(parsed.get('targets', []))}"
    docs[fname] = doc
    print(f"  ✅ {fname} done")
print("✅ Documentation done")

# Step 3: Generate business purpose
print("\n[3/5] Generating business explanations...")
business = {}
for parsed in all_parsed:
    fname = parsed["file"]
    print(f"  Explaining {fname}...")
    exp = explain_business_purpose(parsed)
    if "ERROR" in exp:
        targets = ', '.join(parsed.get('targets', ['data']))
        sources = ', '.join(parsed.get('sources', ['unknown']))
        exp = f"**Business Purpose**\nAutomates data processing from {sources} into {targets}.\n\n**Who Benefits**\nData and analytics teams who depend on {targets} for reporting.\n\n**Risk if Fails**\n{targets} will not be updated causing stale data in reports."
    business[fname] = exp
    print(f"  ✅ {fname} done")
print("✅ Business explanations done")

# Step 4: Generate diagrams
print("\n[4/5] Generating flow diagrams...")
diagrams = {}
for parsed in all_parsed:
    fname = parsed["file"]
    path = generate_flow_diagram(parsed)
    diagrams[fname] = path
print("✅ Diagrams done")

# Step 5: Build RAG vector store
print("\n[5/5] Building RAG vector store...")
rag = RAGPipeline()
rag.build_vector_store(docs)
print("✅ RAG vector store built")

# Save everything to cache
impact_reports, G = analyze_all_scripts(all_parsed)
cache = {
    "parsed": all_parsed,
    "docs": docs,
    "business": business,
    "diagrams": diagrams,
    "impact": {
        "graph_nodes": G.number_of_nodes(),
        "graph_edges": G.number_of_edges(),
        "impact_reports": impact_reports
    }
}
with open(CACHE_FILE, "w") as f:
    json.dump(cache, f, indent=2)

print(f"\n✅ ALL OUTPUTS PRE-GENERATED AND SAVED TO {CACHE_FILE}")
print("Now run the backend and frontend — everything will be instant!")