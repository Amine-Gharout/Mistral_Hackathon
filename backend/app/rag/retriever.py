"""RAG retriever — search the ANAH guide and return relevant chunks."""

from __future__ import annotations

from .embedder import embed_query
from .store import vector_store


def retrieve(
    query: str,
    top_k: int = 5,
    boost_tables: bool = False,
) -> list[dict]:
    """
    Retrieve relevant chunks from the ANAH guide.

    Args:
        query: User query text
        top_k: Number of chunks to retrieve
        boost_tables: Whether to boost table-type chunks (for numeric queries)

    Returns:
        List of chunk dicts with text, metadata, and relevance score
    """
    if not vector_store.chunks:
        return []

    # Auto-detect if we should boost tables
    numeric_keywords = ["combien", "montant", "€",
                        "euro", "plafond", "barème", "tableau"]
    if any(kw in query.lower() for kw in numeric_keywords):
        boost_tables = True

    query_embedding = embed_query(query)
    results = vector_store.search(
        query_embedding, top_k=top_k * 2 if boost_tables else top_k)

    if boost_tables and results:
        # Re-rank: boost table chunks
        for r in results:
            if r.get("chunk_type") == "table":
                r["score"] = r.get("score", 0) * 1.3  # 30% boost
        results.sort(key=lambda x: x.get("score", 0), reverse=True)

    # Apply MMR-like diversity (simple version)
    selected = _mmr_rerank(results, top_k=top_k, lambda_param=0.7)

    return selected


def _mmr_rerank(results: list[dict], top_k: int, lambda_param: float = 0.7) -> list[dict]:
    """
    Simple MMR-like reranking for diversity.
    Penalizes chunks from the same page/section as already selected ones.
    """
    if len(results) <= top_k:
        return results

    selected = []
    remaining = list(results)

    while len(selected) < top_k and remaining:
        if not selected:
            # Pick the highest scoring one first
            best = max(remaining, key=lambda x: x.get("score", 0))
        else:
            # Score = lambda * relevance - (1-lambda) * max_similarity_to_selected
            best = None
            best_mmr = float("-inf")

            selected_pages = {s.get("page_number") for s in selected}
            selected_types = {s.get("aid_type") for s in selected}

            for r in remaining:
                relevance = r.get("score", 0)
                # Penalty for same page or same aid type
                similarity_penalty = 0
                if r.get("page_number") in selected_pages:
                    similarity_penalty += 0.3
                if r.get("aid_type") in selected_types:
                    similarity_penalty += 0.1

                mmr_score = lambda_param * relevance - \
                    (1 - lambda_param) * similarity_penalty
                if mmr_score > best_mmr:
                    best_mmr = mmr_score
                    best = r

        if best:
            selected.append(best)
            remaining.remove(best)
        else:
            break

    return selected


def search_anah_guide(query: str) -> str:
    """
    Tool-callable function for the agent.
    Returns formatted text from relevant ANAH guide chunks.
    """
    chunks = retrieve(query, top_k=5)

    if not chunks:
        return (
            "Aucune information trouvée dans le guide ANAH 2026 pour cette requête. "
            "Vous pouvez consulter directement le guide sur : "
            "https://www.anah.gouv.fr/document/guide-des-aides-financieres-0126"
        )

    parts = []
    for i, chunk in enumerate(chunks, 1):
        page = chunk.get("page_number")
        title = chunk.get("title", "")
        text = chunk.get("text", "")
        page_info = f" (page {page})" if page else ""
        parts.append(f"[Source {i}{page_info}] {title}\n{text}")

    return "\n\n---\n\n".join(parts)
