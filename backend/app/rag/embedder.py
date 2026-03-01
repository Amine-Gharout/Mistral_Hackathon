"""Embedding service using Mistral AI's mistral-embed model."""

from __future__ import annotations

import time
from typing import Optional

import numpy as np
from mistralai import Mistral

from ..config import settings


_client: Optional[Mistral] = None


def _get_client() -> Mistral:
    global _client
    if _client is None:
        _client = Mistral(api_key=settings.MISTRAL_API_KEY)
    return _client


def embed_texts(texts: list[str], batch_size: int = 10) -> np.ndarray:
    """
    Embed a list of texts using mistral-embed.

    Args:
        texts: List of text strings to embed
        batch_size: Number of texts per API call

    Returns:
        numpy array of shape (len(texts), embedding_dim)
    """
    client = _get_client()
    all_embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        retries = 3
        for attempt in range(retries):
            try:
                response = client.embeddings.create(
                    model=settings.MISTRAL_EMBED_MODEL,
                    inputs=batch,
                )
                batch_embs = [item.embedding for item in response.data]
                all_embeddings.extend(batch_embs)
                break
            except Exception as e:
                if attempt < retries - 1:
                    wait = 2 ** attempt
                    print(
                        f"[RAG] Embedding error (attempt {attempt + 1}): {e}. Retrying in {wait}s...")
                    time.sleep(wait)
                else:
                    print(
                        f"[RAG] Embedding failed after {retries} attempts: {e}")
                    # Return zero vectors on failure
                    all_embeddings.extend([[0.0] * 1024] * len(batch))

        # Small delay between batches to respect rate limits
        if i + batch_size < len(texts):
            time.sleep(0.1)

    embeddings = np.array(all_embeddings, dtype=np.float32)

    # L2 normalize for inner-product search
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1  # avoid division by zero
    embeddings = embeddings / norms

    print(f"[RAG] Embedded {len(texts)} texts → shape {embeddings.shape}")
    return embeddings


def embed_query(query: str) -> np.ndarray:
    """Embed a single query text."""
    result = embed_texts([query])
    return result[0]
