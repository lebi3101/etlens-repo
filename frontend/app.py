# frontend/app.py
import streamlit as st
import os
import sys
import json
import tempfile

# Add parent directory to path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from parser.python_parser import parse_python_etl
from parser.sql_parser import parse_sql_etl
from ai.doc_generator import generate_documentation
from ai.business_explainer import explain_business_purpose
from diagram.flow_diagram import generate_flow_diagram
from impact.impact_analysis import analyze_all_scripts, get_impact_analysis, build_dependency_graph
from ai.rag_pipeline import query_rag
from export.pdf_exporter import export_to_pdf

st.set_page_config(
    page_title="ETL Doc Generator",
    page_icon="⚙️",
    layout="wide"
)

st.title("ETL Script Documentation Generator")
st.caption("Automatically generate docs, diagrams, and impact analysis for your ETL scripts.")

# ── SESSION STATE ─────────────────────────────────
if "parsed_files" not in st.session_state:
    st.session_state.parsed_files = []
if "docs" not in st.session_state:
    st.session_state.docs = {}
if "business" not in st.session_state:
    st.session_state.business = {}
if "diagrams" not in st.session_state:
    st.session_state.diagrams = {}
if "impact" not in st.session_state:
    st.session_state.impact = {}

# ── SIDEBAR ───────────────────────────────────────
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", [
    "Analyze Scripts",
    "Documentation",
    "Business Purpose",
    "Flow Diagrams",
    "Impact Analysis",
    "Ask AI"
])

# ── HELPER ───────────────────────────────────────
def parse_file(filepath, filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext == ".py":
        return parse_python_etl(filepath)
    elif ext == ".sql":
        return parse_sql_etl(filepath)
    return None

SAMPLE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "etl_samples"
)

# ── PAGE 1 ───────────────────────────────────────
if page == "Analyze Scripts":
    st.header("Analyze ETL Scripts")

    st.subheader("Use Sample Files")
    if st.button("▶ Analyze Sample ETL Files"):
        with st.spinner("Analyzing sample files..."):
            parsed = []
            for fname in os.listdir(SAMPLE_DIR):
                if fname.endswith(".py") or fname.endswith(".sql"):
                    fpath = os.path.join(SAMPLE_DIR, fname)
                    result = parse_file(fpath, fname)
                    if result:
                        parsed.append(result)
            st.session_state.parsed_files = parsed
            st.success(f"Analyzed {len(parsed)} files!")
            for p in parsed:
                with st.expander(f"{p['file']}"):
                    st.write(f"**Type:** {p['type']}")
                    st.write(f"**Sources:** {', '.join(p['sources']) or 'N/A'}")
                    st.write(f"**Targets:** {', '.join(p['targets']) or 'N/A'}")
                    st.write(f"**Transformations:** {', '.join(p['transformations']) or 'N/A'}")

    st.divider()
    st.subheader("Upload Your Own Files")
    uploaded = st.file_uploader(
        "Upload .py or .sql ETL files",
        type=["py", "sql"],
        accept_multiple_files=True
    )
    if uploaded and st.button("Upload & Analyze"):
        with st.spinner("Parsing uploaded files..."):
            parsed = []
            for f in uploaded:
                suffix = ".py" if f.name.endswith(".py") else ".sql"
                with tempfile.NamedTemporaryFile(
                    delete=False, suffix=suffix, mode="wb"
                ) as tmp:
                    tmp.write(f.getvalue())
                    tmp_path = tmp.name
                result = parse_file(tmp_path, f.name)
                os.unlink(tmp_path)
                if result:
                    result["file"] = f.name
                    parsed.append(result)
            st.session_state.parsed_files = parsed
            st.success(f"Parsed {len(parsed)} files!")
            for p in parsed:
                with st.expander(f"📄 {p['file']}"):
                    st.write(f"**Type:** {p['type']}")
                    st.write(f"**Sources:** {', '.join(p['sources']) or 'N/A'}")
                    st.write(f"**Targets:** {', '.join(p['targets']) or 'N/A'}")
                    st.write(f"**Transformations:** {', '.join(p['transformations']) or 'N/A'}")

# ── PAGE 2 ───────────────────────────────────────
elif page == "Documentation":
    st.header("Auto-Generated Documentation")
    if not st.session_state.parsed_files:
        st.warning("Please analyze scripts first from the 'Analyze Scripts' page.")
    else:
        if st.button("Generate Documentation"):
            with st.spinner("Generating docs with AI..."):
                docs = {}
                for p in st.session_state.parsed_files:
                    doc = generate_documentation(p)
                    docs[p["file"]] = doc
                st.session_state.docs = docs
                # Build RAG index immediately after generating docs
                from ai.rag_pipeline import build_rag_index
                build_rag_index(docs)
                st.success(f"Generated docs for {len(docs)} files!")
        if st.session_state.docs:
            for fname, doc in st.session_state.docs.items():
                with st.expander(f"{fname}"):
                    st.markdown(doc)

# ── PAGE 3 ───────────────────────────────────────
elif page == "Business Purpose":
    st.header("Business Purpose Explainer")
    if not st.session_state.parsed_files:
        st.warning("Please analyze scripts first from the 'Analyze Scripts' page.")
    else:
        if st.button("Explain Business Purpose"):
            with st.spinner("Analyzing business context..."):
                business = {}
                for p in st.session_state.parsed_files:
                    explanation = explain_business_purpose(p)
                    business[p["file"]] = explanation
                st.session_state.business = business
                st.success(f"Explained {len(business)} scripts!")
        if st.session_state.business:
            for fname, explanation in st.session_state.business.items():
                with st.expander(f"{fname}"):
                    st.markdown(explanation)

# ── PAGE 4 ───────────────────────────────────────
elif page == "Flow Diagrams":
    st.header("Data Flow Diagrams")
    if not st.session_state.parsed_files:
        st.warning("Please analyze scripts first from the 'Analyze Scripts' page.")
    else:
        if st.button("Generate Flow Diagrams"):
            with st.spinner("Generating diagrams..."):
                diagrams = {}
                for p in st.session_state.parsed_files:
                    path = generate_flow_diagram(p)
                    diagrams[p["file"]] = path
                st.session_state.diagrams = diagrams
                st.success(f"Generated {len(diagrams)} diagrams!")
        if st.session_state.diagrams:
            for fname, path in st.session_state.diagrams.items():
                st.subheader(f"{fname}")
                if path and os.path.exists(path):
                    st.image(path)
                else:
                    st.warning(f"Diagram not found for {fname}")

# ── PAGE 5 ───────────────────────────────────────
elif page == "Impact Analysis":
    st.header("Impact Analysis")
    if not st.session_state.parsed_files:
        st.warning("Please analyze scripts first from the 'Analyze Scripts' page.")
    else:
        if st.button("Run Impact Analysis"):
            with st.spinner("Analyzing dependencies..."):
                results, G = analyze_all_scripts(st.session_state.parsed_files)
                impact = results
                st.session_state.impact = impact
                st.success("Impact analysis complete!")
        if st.session_state.impact:
            for fname, report in st.session_state.impact.items():
                risk = report.get("risk_level", "N/A")
                color = {
                    "LOW": "🟢",
                    "MEDIUM": "🟡",
                    "HIGH": "🔴"
                }.get(risk, "⚪")
                with st.expander(f"{color} {fname} — Risk: {risk}"):
                    st.write(f"**Reason:** {report.get('risk_reason')}")
                    st.write(f"**Depends on:** {report.get('upstream_dependencies') or 'None'}")
                    st.write(f"**Writes to:** {report.get('direct_outputs') or 'None'}")
                    st.write(f"**Affected scripts:** {report.get('affected_scripts') or 'None'}")
                    st.write(f"**Total nodes affected:** {report.get('total_nodes_affected')}")

# ── PAGE 6 ───────────────────────────────────────
elif page == "Ask AI":
    st.header("Ask AI About Your ETL Scripts")
    st.info("Generate documentation first so the AI has context to work with.")
    question = st.text_input(
        "Ask a question:",
        placeholder="What does the HR script do?"
    )
    if st.button("Ask") and question:
        with st.spinner("Thinking..."):
            answer = query_rag(question)
            st.markdown(f"**Answer:** {answer}")

# ── SIDEBAR DOWNLOAD ──────────────────────────────
st.sidebar.divider()
st.sidebar.subheader("Export")
if st.sidebar.button("Download PDF Report"):
    if not st.session_state.docs:
        st.sidebar.error("Generate documentation first!")
    else:
        with st.spinner("Generating PDF..."):
            # Build parsed lookup dict
            parsed_lookup = {
                p["file"]: p 
                for p in st.session_state.parsed_files
            }
            pdf_bytes = export_to_pdf(
                st.session_state.docs,
                st.session_state.business,
                st.session_state.impact,
                parsed_lookup
            )
            st.sidebar.download_button(
                label="Click to Save PDF",
                data=pdf_bytes,
                file_name="etl_report.pdf",
                mime="application/pdf"
            )