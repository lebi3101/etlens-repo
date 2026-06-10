import os
import sys

print("=" * 50)
print("ETL Doc Generator — Environment Check")
print("=" * 50)

# Check 1 — Python version
print(f"\n✅ Python Version: {sys.version}")

# Check 2 — All imports
print("\nChecking all package imports...")
packages = {
    "fastapi": "FastAPI",
    "uvicorn": "Uvicorn",
    "streamlit": "Streamlit",
    "langchain": "LangChain",
    "faiss": "FAISS",
    "sqlparse": "sqlparse",
    "networkx": "NetworkX",
    "fpdf": "fpdf2",
    "graphviz": "Graphviz",
    "sentence_transformers": "Sentence Transformers",
    "sqlalchemy": "SQLAlchemy",
    "dotenv": "python-dotenv",
    "requests": "Requests",
    "markdown": "Markdown",
}

all_ok = True
for package, name in packages.items():
    try:
        __import__(package)
        print(f"  ✅ {name}")
    except ImportError:
        print(f"  ❌ {name} — NOT FOUND")
        all_ok = False

# Check 3 — .env file
print("\nChecking .env file...")
from dotenv import load_dotenv
load_dotenv()
ollama_url = os.getenv("OLLAMA_BASE_URL")
ollama_model = os.getenv("OLLAMA_MODEL")
output_dir = os.getenv("OUTPUT_DIR")
db_path = os.getenv("DB_PATH")

if ollama_url:
    print(f"  ✅ OLLAMA_BASE_URL = {ollama_url}")
else:
    print("  ❌ OLLAMA_BASE_URL missing in .env")
    all_ok = False

if ollama_model:
    print(f"  ✅ OLLAMA_MODEL = {ollama_model}")
else:
    print("  ❌ OLLAMA_MODEL missing in .env")
    all_ok = False

if output_dir:
    print(f"  ✅ OUTPUT_DIR = {output_dir}")
else:
    print("  ❌ OUTPUT_DIR missing in .env")
    all_ok = False

if db_path:
    print(f"  ✅ DB_PATH = {db_path}")
else:
    print("  ❌ DB_PATH missing in .env")
    all_ok = False

# Check 4 — Ollama connection
print("\nChecking Ollama connection...")
import requests
try:
    response = requests.get(ollama_url)
    if "running" in response.text.lower():
        print(f"  ✅ Ollama is running at {ollama_url}")
    else:
        print(f"  ❌ Ollama responded but unexpectedly: {response.text}")
        all_ok = False
except Exception as e:
    print(f"  ❌ Cannot connect to Ollama: {e}")
    all_ok = False

# Check 5 — Ollama model availability
print("\nChecking Llama3 model...")
try:
    response = requests.get(f"{ollama_url}/api/tags")
    models = response.json().get("models", [])
    model_names = [m["name"] for m in models]
    if any("llama3" in m for m in model_names):
        print(f"  ✅ Llama3 model found: {model_names}")
    else:
        print(f"  ❌ Llama3 not found. Available: {model_names}")
        print("     Run: ollama pull llama3")
        all_ok = False
except Exception as e:
    print(f"  ❌ Could not check models: {e}")
    all_ok = False

# Check 6 — Output folders
print("\nChecking output folders...")
folders = ["output/docs", "output/diagrams", "output/reports"]
for folder in folders:
    if os.path.exists(folder):
        print(f"  ✅ {folder} exists")
    else:
        os.makedirs(folder)
        print(f"  ✅ {folder} created")

# Check 7 — Graphviz binary
print("\nChecking Graphviz binary...")
import graphviz
try:
    dot = graphviz.Digraph()
    dot.node("A", "Test")
    dot.node("B", "Node")
    dot.edge("A", "B")
    dot.render("output/diagrams/test_diagram", format="png", cleanup=True)
    print("  ✅ Graphviz rendered a test diagram successfully")
    print("  ✅ Check output/diagrams/ for test_diagram.png")
except Exception as e:
    print(f"  ❌ Graphviz error: {e}")
    all_ok = False

# Final result
print("\n" + "=" * 50)
if all_ok:
    print("🎉 ALL CHECKS PASSED — Environment is fully ready!")
else:
    print("⚠️  SOME CHECKS FAILED — Fix the errors above first")
print("=" * 50)