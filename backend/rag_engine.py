"""
rag_engine.py
-------------
RAG support using SentenceTransformer + FAISS.

Optimized for faster CSV uploads by:
- Loading the embedding model only once
- Processing rows in batches
- Using normalized embeddings for cosine similarity
- Limiting the amount of text indexed
"""

import uuid
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer


# Small and fast embedding model
EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"

# Number of rows processed at once
BATCH_SIZE = 64

# Maximum number of rows indexed
# Increase this if your CSV is small.
MAX_CHUNKS = 5000


class RAGEngine:

    def __init__(self, persist_directory: str = "./faiss_store"):

        self.persist_directory = persist_directory

        print("Loading embedding model...")

        self.embedder = SentenceTransformer(
            EMBEDDING_MODEL_NAME
        )

        print("Embedding model loaded.")

        self.index = None
        self.chunks = []
        self.session_id = None

    # ---------------------------------------------------------
    def build_index(
        self,
        chunks: list[str],
        session_id: str | None = None
    ):
        """
        Build FAISS index from CSV text chunks.
        """

        self.session_id = (
            session_id or uuid.uuid4().hex[:8]
        )

        # Clear previous index
        self.index = None
        self.chunks = []

        if not chunks:
            print("No chunks available for RAG.")
            return

        # Limit number of chunks
        if len(chunks) > MAX_CHUNKS:

            print(
                f"CSV contains {len(chunks)} rows. "
                f"Indexing first {MAX_CHUNKS} rows."
            )

            chunks = chunks[:MAX_CHUNKS]

        print(
            f"Creating embeddings for {len(chunks)} rows..."
        )

        # -----------------------------------------------------
        # Generate embeddings in batches
        # -----------------------------------------------------

        embeddings = self.embedder.encode(
            chunks,
            batch_size=BATCH_SIZE,
            show_progress_bar=True,
            convert_to_numpy=True
        )

        # Convert to float32
        embeddings = np.asarray(
            embeddings,
            dtype=np.float32
        )

        # Normalize for cosine similarity
        faiss.normalize_L2(embeddings)

        # -----------------------------------------------------
        # Create FAISS index
        # -----------------------------------------------------

        dimension = embeddings.shape[1]

        self.index = faiss.IndexFlatIP(
            dimension
        )

        # Add embeddings
        self.index.add(
            embeddings
        )

        # Store chunks
        self.chunks = list(chunks)

        print(
            f"FAISS index created successfully "
            f"with {self.index.ntotal} vectors."
        )

    # ---------------------------------------------------------
    def retrieve(
        self,
        query: str,
        top_k: int = 5
    ) -> list[str]:
        """
        Return the most relevant chunks.
        """

        if (
            self.index is None
            or not self.chunks
        ):
            return []

        # Create embedding for user question
        query_embedding = self.embedder.encode(
            [query],
            show_progress_bar=False,
            convert_to_numpy=True
        )

        query_embedding = np.asarray(
            query_embedding,
            dtype=np.float32
        )

        # Normalize
        faiss.normalize_L2(
            query_embedding
        )

        # Number of results
        k = min(
            top_k,
            len(self.chunks)
        )

        # Search FAISS
        distances, indices = self.index.search(
            query_embedding,
            k
        )

        results = []

        for idx in indices[0]:

            if idx != -1:
                results.append(
                    self.chunks[idx]
                )

        return results

    # ---------------------------------------------------------
    def clear(self):
        """
        Clear the current FAISS index.
        """

        self.index = None
        self.chunks = []
        self.session_id = None

        print("RAG index cleared.")