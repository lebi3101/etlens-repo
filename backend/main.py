import sys, os, json, shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from parser.python_parser import parse_python_etl
from parser.sql_parser import parse_sql_etl
from ai.doc_generator import generate_documentation
from ai.business_explainer import explain_business_purpose
from diagram.flow_diagram import generate_flow_diagram
from impact.impact_analysis import build_dependency_graph, get_impact_analysis, analyze_all_scripts
from ai.rag_pipeline import RAGPipeline
from export.pdf_exporter import generate_pdf_report

app = FastAPI(title="ETL Doc Generator API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
UPLOAD_DIR = os.path.join(OUTPUT_DIR, "uploads")
CACHE_FILE = "output/pregenerated_cache.json"
os.makedirs(UPLOAD_DIR, exist_ok=True)

rag = RAGPipeline()
all_parsed_cache = []
all_docs_cache = {}
DEMO_CACHE = None


def load_cache():
    global DEMO_CACHE
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as f:
            DEMO_CACHE = json.load(f)
        print("✅ Pre-generated cache loaded!")
    return DEMO_CACHE


load_cache()


def parse_file(filepath: str) -> dict:
    if filepath.endswith(".py"):
        return parse_python_etl(filepath)
    elif filepath.endswith(".sql"):
        return parse_sql_etl(filepath)
    return None


def generate_instant_doc(parsed: dict) -> str:
    fname = parsed.get("file", "unknown")
    sources = ', '.join(parsed.get("sources", [])) or "N/A"
    targets = ', '.join(parsed.get("targets", [])) or "N/A"
    transforms = ', '.join(parsed.get("transformations", [])) or "N/A"
    script_type = parsed.get("type", "python").upper()
    return f"""**Overview**
{fname} is a {script_type} ETL script that reads data from {sources}, applies transformations, and loads results into {targets}.

**What It Does**
- Reads from: {sources}
- Applies: {transforms}
- Writes to: {targets}

**Technical Summary**
- Script Type: {script_type}
- Input(s): {sources}
- Output(s): {targets}
- Operations: {transforms}"""


def generate_instant_business(parsed: dict) -> str:
    fname = parsed.get("file", "unknown")
    sources = ', '.join(parsed.get("sources", [])) or "unknown sources"
    targets = ', '.join(parsed.get("targets", [])) or "unknown targets"
    return f"""**Business Purpose**
This script automates processing of data from {sources} into {targets}, eliminating manual data handling and ensuring data is always current.

**Who Benefits**
Data and analytics teams who depend on {targets} for reporting, dashboards, and business decisions.

**Risk if Fails**
If {fname} fails, {targets} will not be updated — causing stale or missing data in all downstream reports."""

class QuestionRequest(BaseModel):
    question: str
# ── ROUTES ──────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "ETL Doc Generator API is running!"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    uploaded = []
    for file in files:
        dest = os.path.join(UPLOAD_DIR, file.filename)
        with open(dest, "wb") as f:
            shutil.copyfileobj(file.file, f)
        uploaded.append(file.filename)
    return {"uploaded": uploaded, "count": len(uploaded)}


@app.get("/analyze")
def analyze_all():
    global all_parsed_cache
    all_parsed_cache = []
    files = os.listdir(UPLOAD_DIR)
    file_dir = UPLOAD_DIR if files else "etl_samples"
    if not files:
        files = os.listdir("etl_samples")
    for fname in files:
        fpath = os.path.join(file_dir, fname)
        parsed = parse_file(fpath)
        if parsed:
            all_parsed_cache.append(parsed)
    return {"files_analyzed": len(all_parsed_cache), "parsed": all_parsed_cache}


@app.get("/sample/analyze")
def analyze_samples():
    global all_parsed_cache
    all_parsed_cache = []
    for fname in os.listdir("etl_samples"):
        fpath = os.path.join("etl_samples", fname)
        parsed = parse_file(fpath)
        if parsed:
            all_parsed_cache.append(parsed)
    return {"files_analyzed": len(all_parsed_cache), "parsed": all_parsed_cache}


@app.get("/docs/generate")
def generate_all_docs():
    global all_docs_cache
    if not all_parsed_cache:
        analyze_samples()

    cached_files = list(DEMO_CACHE["docs"].keys()) if DEMO_CACHE and "docs" in DEMO_CACHE else []
    all_docs_cache = {}
    results = []

    for parsed in all_parsed_cache:
        fname = parsed["file"]
        if fname in cached_files:
            doc = DEMO_CACHE["docs"][fname]
        else:
            doc = generate_instant_doc(parsed)
        all_docs_cache[fname] = doc
        results.append({"file": fname, "documentation": doc})

    if all_docs_cache:
        rag.build_vector_store(all_docs_cache)

    return {"count": len(results), "documents": results}


@app.get("/docs/business")
def generate_business_docs():
    if not all_parsed_cache:
        analyze_samples()

    cached_files = list(DEMO_CACHE["business"].keys()) if DEMO_CACHE and "business" in DEMO_CACHE else []
    results = []

    for parsed in all_parsed_cache:
        fname = parsed["file"]
        if fname in cached_files:
            explanation = DEMO_CACHE["business"][fname]
        else:
            explanation = generate_instant_business(parsed)
        results.append({"file": fname, "business_purpose": explanation})

    return {"count": len(results), "explanations": results}


@app.get("/diagrams/generate")
def generate_diagrams():
    if not all_parsed_cache:
        analyze_samples()
    results = []
    for parsed in all_parsed_cache:
        path = generate_flow_diagram(parsed)
        results.append({"file": parsed["file"], "diagram_path": path})
    return {"count": len(results), "diagrams": results}


@app.get("/impact")
def impact_analysis():
    if not all_parsed_cache:
        analyze_samples()
    results, G = analyze_all_scripts(all_parsed_cache)
    return {
        "graph_nodes": G.number_of_nodes(),
        "graph_edges": G.number_of_edges(),
        "impact_reports": results
    }


@app.post("/ask")
def ask_question(request: QuestionRequest):
    if rag.index is None:
        loaded = rag.load()
        if not loaded:
            raise HTTPException(status_code=400, detail="No vector store found. Call /docs/generate first.")
    answer = rag.ask(request.question)
    return {"question": request.question, "answer": answer}


@app.get("/export/pdf")
def export_pdf():
    if not all_parsed_cache:
        analyze_samples()
    docs = all_docs_cache if all_docs_cache else {p["file"]: generate_instant_doc(p) for p in all_parsed_cache}
    business = {p["file"]: generate_instant_business(p) for p in all_parsed_cache}
    impact_reports, _ = analyze_all_scripts(all_parsed_cache)
    path = generate_pdf_report(all_parsed_cache, docs, business, impact_reports)
    return FileResponse(path, media_type="application/pdf", filename="etl_report.pdf")


@app.post("/test/parse")
async def test_parse(file: UploadFile = File(...)):
    dest = os.path.join(UPLOAD_DIR, file.filename)
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    parsed = parse_file(dest)
    if not parsed:
        return {"error": "Unsupported file type. Use .py or .sql"}
    return parsed