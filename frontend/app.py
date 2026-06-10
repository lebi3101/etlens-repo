import streamlit as st
import requests
import os

API_URL = "http://127.0.0.1:8000"

st.set_page_config(
    page_title="ETL Doc Generator",
    page_icon="⚙️",
    layout="wide"
)

st.title("⚙️ ETL Script Documentation Generator")
st.caption("Automatically generate docs, diagrams, and impact analysis for your ETL scripts.")

# Sidebar
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", [
    "📂 Analyze Scripts",
    "📄 Documentation",
    "💼 Business Purpose",
    "🔀 Flow Diagrams",
    "💥 Impact Analysis",
    "🤖 Ask AI"
])

# ── PAGE 1 ──────────────────────────────────────────
if page == "📂 Analyze Scripts":
    st.header("📂 Analyze ETL Scripts")

    st.subheader("Use Sample Files")
    if st.button("▶ Analyze Sample ETL Files"):
        with st.spinner("Analyzing..."):
            res = requests.get(f"{API_URL}/sample/analyze")
            if res.status_code == 200:
                data = res.json()
                st.success(f"✅ Analyzed {data['files_analyzed']} files!")
                for p in data["parsed"]:
                    with st.expander(f"📄 {p['file']}"):
                        st.write(f"**Type:** {p['type']}")
                        st.write(f"**Sources:** {', '.join(p['sources']) or 'N/A'}")
                        st.write(f"**Targets:** {', '.join(p['targets']) or 'N/A'}")
                        st.write(f"**Transformations:** {', '.join(p['transformations']) or 'N/A'}")
            else:
                st.error("Failed to analyze files.")

    st.divider()
    st.subheader("Upload Your Own Files")
    uploaded = st.file_uploader(
        "Upload .py or .sql ETL files",
        type=["py", "sql"],
        accept_multiple_files=True
    )
    if uploaded and st.button("📤 Upload & Analyze"):
        with st.spinner("Uploading..."):
            files = [("files", (f.name, f.getvalue())) for f in uploaded]
            res = requests.post(f"{API_URL}/upload", files=files)
            if res.status_code == 200:
                st.success(f"✅ Uploaded: {res.json()['uploaded']}")
                res2 = requests.get(f"{API_URL}/analyze")
                if res2.status_code == 200:
                    data = res2.json()
                    st.success(f"Analyzed {data['files_analyzed']} files!")
                    for p in data["parsed"]:
                        with st.expander(f"📄 {p['file']}"):
                            st.json(p)

# ── PAGE 2 ──────────────────────────────────────────
elif page == "📄 Documentation":
    st.header("📄 Auto-Generated Documentation")
    st.info("This calls the LLM — may take 2-4 minutes.")
    if st.button("⚡ Generate Documentation"):
        with st.spinner("Generating docs with AI... please wait"):
            res = requests.get(f"{API_URL}/docs/generate", timeout=600)
            if res.status_code == 200:
                data = res.json()
                st.success(f"✅ Generated docs for {data['count']} files!")
                for doc in data["documents"]:
                    with st.expander(f"📄 {doc['file']}"):
                        st.markdown(doc["documentation"])
            else:
                st.error("Failed to generate documentation.")

# ── PAGE 3 ──────────────────────────────────────────
elif page == "💼 Business Purpose":
    st.header("💼 Business Purpose Explainer")
    st.info("This calls the LLM — may take 2-4 minutes.")
    if st.button("💡 Explain Business Purpose"):
        with st.spinner("Analyzing business context..."):
            res = requests.get(f"{API_URL}/docs/business", timeout=600)
            if res.status_code == 200:
                data = res.json()
                st.success(f"✅ Explained {data['count']} scripts!")
                for item in data["explanations"]:
                    with st.expander(f"💼 {item['file']}"):
                        st.markdown(item["business_purpose"])
            else:
                st.error("Failed to generate explanations.")

# ── PAGE 4 ──────────────────────────────────────────
elif page == "🔀 Flow Diagrams":
    st.header("🔀 Data Flow Diagrams")
    if st.button("🎨 Generate Flow Diagrams"):
        with st.spinner("Generating diagrams..."):
            res = requests.get(f"{API_URL}/diagrams/generate", timeout=120)
            if res.status_code == 200:
                data = res.json()
                st.success(f"✅ Generated {data['count']} diagrams!")
                for item in data["diagrams"]:
                    st.subheader(f"📊 {item['file']}")
                    path = item["diagram_path"]
                    if os.path.exists(path):
                        st.image(path)
                    else:
                        st.warning(f"Diagram file not found at: {path}")
            else:
                st.error("Failed to generate diagrams.")

# ── PAGE 5 ──────────────────────────────────────────
elif page == "💥 Impact Analysis":
    st.header("💥 Impact Analysis")
    if st.button("🔍 Run Impact Analysis"):
        with st.spinner("Analyzing dependencies..."):
            res = requests.get(f"{API_URL}/impact", timeout=120)
            if res.status_code == 200:
                data = res.json()
                st.success(f"✅ Graph: {data['graph_nodes']} nodes, {data['graph_edges']} edges")
                for fname, report in data["impact_reports"].items():
                    risk = report.get("risk_level", "N/A")
                    color = {"LOW": "🟢", "MEDIUM": "🟡", "HIGH": "🔴"}.get(risk, "⚪")
                    with st.expander(f"{color} {fname} — Risk: {risk}"):
                        st.write(f"**Reason:** {report.get('risk_reason')}")
                        st.write(f"**Depends on:** {report.get('upstream_dependencies') or 'None'}")
                        st.write(f"**Writes to:** {report.get('direct_outputs') or 'None'}")
                        st.write(f"**Affected scripts:** {report.get('affected_scripts') or 'None'}")
                        st.write(f"**Total nodes affected:** {report.get('total_nodes_affected')}")
            else:
                st.error("Failed to run impact analysis.")

# ── PAGE 6 ──────────────────────────────────────────
elif page == "🤖 Ask AI":
    st.header("🤖 Ask AI About Your ETL Scripts")
    st.info("Generate documentation first so the AI has context to work with.")
    question = st.text_input("Ask a question:", placeholder="What does the HR script do?")
    if st.button("🔍 Ask") and question:
        with st.spinner("Thinking..."):
            res = requests.post(
                f"{API_URL}/ask",
                json={"question": question},
                timeout=300
            )
            if res.status_code == 200:
                st.markdown(f"**Answer:** {res.json()['answer']}")
            else:
                st.error(f"Error: {res.json().get('detail', 'Unknown error')}")

# ── SIDEBAR DOWNLOAD ─────────────────────────────────
st.sidebar.divider()
st.sidebar.subheader("📥 Export")
if st.sidebar.button("⬇️ Download PDF Report"):
    with st.spinner("Generating PDF..."):
        res = requests.get(f"{API_URL}/export/pdf", timeout=120)
        if res.status_code == 200:
            st.sidebar.download_button(
                label="📄 Click to Save PDF",
                data=res.content,
                file_name="etl_report.pdf",
                mime="application/pdf"
            )
        else:
            st.sidebar.error("Analyze scripts first!")