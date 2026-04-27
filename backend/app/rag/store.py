"""FAISS vector store for RAG chunks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import numpy as np

try:
    import faiss
except ImportError:
    faiss = None
    print("[RAG] WARNING: faiss-cpu not installed. Vector search will be unavailable.")

from ..config import settings


class VectorStore:
    """FAISS-based vector store for document chunks."""

    def __init__(self):
        self.index: Optional[object] = None
        self.chunks: list[dict] = []
        self.dimension: int = 1024  # mistral-embed dimension

    def build_index(self, embeddings: np.ndarray, chunks: list[dict]):
        """Build FAISS index from embeddings and chunk metadata."""
        if faiss is None:
            print("[RAG] FAISS not available, skipping index build.")
            self.chunks = chunks
            return

        self.dimension = embeddings.shape[1]
        # Inner product (on normalized vectors = cosine)
        self.index = faiss.IndexFlatIP(self.dimension)
        self.index.add(embeddings)
        self.chunks = chunks
        print(
            f"[RAG] Built FAISS index with {self.index.ntotal} vectors (dim={self.dimension})")

    def search(self, query_embedding: np.ndarray, top_k: int = 5) -> list[dict]:
        """Search for most similar chunks."""
        if self.index is None or faiss is None:
            # Fallback: return all chunks (no vector search)
            return self.chunks[:top_k]

        query_vec = query_embedding.reshape(1, -1).astype(np.float32)
        scores, indices = self.index.search(
            query_vec, min(top_k, self.index.ntotal))

        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx >= len(self.chunks):
                continue
            chunk = self.chunks[idx].copy()
            chunk["score"] = float(score)
            results.append(chunk)

        return results

    def save(self, index_path: Optional[Path] = None, meta_path: Optional[Path] = None):
        """Save FAISS index and chunk metadata to disk."""
        idx_path = index_path or settings.FAISS_INDEX_PATH
        mta_path = meta_path or settings.CHUNKS_META_PATH

        if self.index is not None and faiss is not None:
            faiss.write_index(self.index, str(idx_path))
            print(f"[RAG] Saved FAISS index to {idx_path}")

        with open(mta_path, "w", encoding="utf-8") as f:
            json.dump(self.chunks, f, ensure_ascii=False, indent=2)
        print(f"[RAG] Saved {len(self.chunks)} chunk metadata to {mta_path}")

    def load(self, index_path: Optional[Path] = None, meta_path: Optional[Path] = None) -> bool:
        """Load FAISS index and chunk metadata from disk."""
        idx_path = index_path or settings.FAISS_INDEX_PATH
        mta_path = meta_path or settings.CHUNKS_META_PATH

        if not mta_path.exists():
            return False

        with open(mta_path, "r", encoding="utf-8") as f:
            self.chunks = json.load(f)

        if idx_path.exists() and faiss is not None:
            self.index = faiss.read_index(str(idx_path))
            self.dimension = self.index.d
            print(
                f"[RAG] Loaded FAISS index ({self.index.ntotal} vectors) and {len(self.chunks)} chunks from disk")
            return True

        print(f"[RAG] Loaded {len(self.chunks)} chunks (no FAISS index)")
        return True


# Singleton store
vector_store = VectorStore()
