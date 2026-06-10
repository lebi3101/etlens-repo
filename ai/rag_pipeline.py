import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle
from ai.llm_client import query_llm
from dotenv import load_dotenv

load_dotenv()

OUTPUT_DIR = os.getenv("OUTPUT_DIR", "output")
VECTOR_STORE_PATH = os.path.join(OUTPUT_DIR, "vector_store.pkl")

# Load the embedding model once at module level
print("Loading embedding model...")
EMBEDDING_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
print("Embedding model loaded.")


class RAGPipeline:
    def __init__(self):
        self.index = None          # FAISS index
        self.documents = []        # Raw text chunks
        self.metadata = []         # Which file each chunk belongs to

    def build_vector_store(self, docs: dict):
        """
        Takes a dict of {filename: documentation_text} and builds FAISS index.

        Args:
            docs: Dict mapping filename -> documentation string
        """
        self.documents = []
        self.metadata = []
        texts = []

        for filename, doc_text in docs.items():
            # Split doc into chunks of ~200 words for better retrieval
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

        print(f"  Building FAISS index from {len(texts)} chunks...")

        # Generate embeddings
        embeddings = EMBEDDING_MODEL.encode(texts, show_progress_bar=False)
        embeddings = np.array(embeddings).astype("float32")

        # Build FAISS index
        dimension = embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(embeddings)

        print(f"  FAISS index built with {self.index.ntotal} vectors.")

        # Save to disk
        self._save()

    def _save(self):
        """Save index and documents to disk."""
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        with open(VECTOR_STORE_PATH, "wb") as f:
            pickle.dump({
                "documents": self.documents,
                "metadata": self.metadata,
                "embeddings_dim": self.index.d,
                "index": faiss.serialize_index(self.index)
            }, f)
        print(f"  Vector store saved to {VECTOR_STORE_PATH}")

    def load(self):
        """Load index and documents from disk."""
        if not os.path.exists(VECTOR_STORE_PATH):
            print("  No vector store found. Build one first.")
            return False
        with open(VECTOR_STORE_PATH, "rb") as f:
            data = pickle.load(f)
        self.documents = data["documents"]
        self.metadata = data["metadata"]
        self.index = faiss.deserialize_index(data["index"])
        print(f"  Vector store loaded: {self.index.ntotal} vectors.")
        return True

    def retrieve(self, query: str, top_k: int = 3) -> list:
        """
        Finds the most relevant document chunks for a query.

        Args:
            query: The user's question
            top_k: Number of chunks to retrieve

        Returns:
            List of (chunk_text, filename) tuples
        """
        if self.index is None:
            return []

        query_embedding = EMBEDDING_MODEL.encode([query])
        query_embedding = np.array(query_embedding).astype("float32")

        distances, indices = self.index.search(query_embedding, top_k)

        results = []
        for idx in indices[0]:
            if idx < len(self.documents):
                results.append((self.documents[idx], self.metadata[idx]))
        return results

    def ask(self, question: str) -> str:
        """
        Answers a question using RAG:
        retrieve relevant context → send to LLM → return answer.

        Args:
            question: Natural language question about the ETL scripts

        Returns:
            LLM answer string
        """
        if self.index is None:
            loaded = self.load()
            if not loaded:
                return "No documentation found. Please generate docs first."

        # Retrieve relevant chunks
        relevant_chunks = self.retrieve(question, top_k=3)

        if not relevant_chunks:
            return "Could not find relevant context to answer your question."

        # Build context string
        context = "\n\n".join([
            f"From {filename}:\n{chunk}"
            for chunk, filename in relevant_chunks
        ])

        # Trim context to avoid timeout
        trimmed_context = context[:800]

        prompt = f"""Use this ETL documentation context to answer briefly:

{trimmed_context}

Question: {question}
Answer in 2-3 sentences only."""

        return query_llm(prompt)


if __name__ == "__main__":
    print("RAG Pipeline ready. Test via the FastAPI backend.")