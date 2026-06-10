import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import faiss
import numpy as np
import pickle
from ai.llm_client import query_llm
from dotenv import load_dotenv

load_dotenv()

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
VECTOR_STORE_PATH = os.path.join(OUTPUT_DIR, "vector_store.pkl")

# Lazy-loaded — not loaded at import time
_EMBEDDING_MODEL = None

def get_embedding_model():
    """Load embedding model only when first needed."""
    global _EMBEDDING_MODEL
    if _EMBEDDING_MODEL is None:
        from sentence_transformers import SentenceTransformer
        print("Loading embedding model...")
        _EMBEDDING_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        print("Embedding model loaded.")
    return _EMBEDDING_MODEL


class RAGPipeline:
    def __init__(self):
        self.index = None
        self.documents = []
        self.metadata = []

    def build_vector_store(self, docs: dict):
        model = get_embedding_model()
        self.documents = []
        self.metadata = []
        texts = []

        for filename, doc_text in docs.items():
            words = doc_text.split()
            chunk_size = 200
            chunks = [
                " ".join(words[i:i+chunk_size])
                for i in range(0, len(words), chunk_size)
            ]
            for chunk in chunks:
                self.documents.append(chunk)
                self.metadata.append(filename)
                texts.append(chunk)

        embeddings = model.encode(texts, show_progress_bar=False)
        embeddings = np.array(embeddings).astype("float32")

        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)

        self._save()

    def _save(self):
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(VECTOR_STORE_PATH, "wb") as f:
            pickle.dump({
                "documents": self.documents,
                "metadata": self.metadata,
                "embeddings_dim": self.index.d,
                "index": faiss.serialize_index(self.index)
            }, f)

    def load(self):
        if not os.path.exists(VECTOR_STORE_PATH):
            return False
        with open(VECTOR_STORE_PATH, "rb") as f:
            data = pickle.load(f)
        self.documents = data["documents"]
        self.metadata = data["metadata"]
        self.index = faiss.deserialize_index(data["index"])
        return True

    def retrieve(self, query: str, top_k: int = 3) -> list:
        if self.index is None:
            return []
        model = get_embedding_model()
        query_embedding = model.encode([query])
        query_embedding = np.array(query_embedding).astype("float32")
        distances, indices = self.index.search(query_embedding, top_k)
        results = []
        for idx in indices[0]:
            if idx < len(self.documents):
                results.append((self.documents[idx], self.metadata[idx]))
        return results

    def ask(self, question: str) -> str:
        if self.index is None:
            loaded = self.load()
            if not loaded:
                return "No documentation found. Please generate docs first."

        relevant_chunks = self.retrieve(question, top_k=3)
        if not relevant_chunks:
            return "Could not find relevant context to answer your question."

        context = "\n\n".join([
            f"From {filename}:\n{chunk}"
            for chunk, filename in relevant_chunks
        ])
        trimmed_context = context[:800]

        prompt = f"""Use this ETL documentation context to answer briefly:

{trimmed_context}

Question: {question}
Answer in 2-3 sentences only."""

        return query_llm(prompt)


# Global pipeline instance
_pipeline = RAGPipeline()


def query_rag(question: str) -> str:
    """
    Public function called by frontend/app.py.
    Answers a question using the RAG pipeline.
    """
    return _pipeline.ask(question)


def build_rag_index(docs: dict):
    """
    Public function to build the vector store from generated docs.
    Call this after generating documentation.
    """
    _pipeline.build_vector_store(docs)git commit -m "Add query_rag function to rag_pipeline"
    