"""GreenRights FastAPI application entry point."""

from __future__ import annotations

import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import chat, calculate, report
from .services.session_store import session_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown tasks."""
    print("[GreenRights] Starting up...")

    # Initialize RAG index in background
    try:
        from .rag.store import vector_store
        if vector_store.index is None:
            # Try to load existing index first
            loaded = vector_store.load()
            if not loaded:
                print(
                    "[GreenRights] No existing FAISS index found. Building new index...")
                from .rag.loader import load_pdf
                from .rag.chunker import chunk_pages
                from .rag.embedder import embed_texts

                pdf_path = settings.ANAH_PDF_PATH
                if pdf_path.exists():
                    pages = load_pdf(pdf_path)
                    chunks = chunk_pages(pages)
                else:
                    print("[GreenRights] PDF not found, using fallback chunks")
                    from .rag.chunker import _get_fallback_chunks
                    chunks = _get_fallback_chunks()

                texts = [c["text"] for c in chunks]
                embeddings = embed_texts(texts)
                vector_store.build_index(embeddings, chunks)
                vector_store.save()
                print(
                    f"[GreenRights] FAISS index built with {len(chunks)} chunks")
            else:
                print(
                    f"[GreenRights] FAISS index loaded with {vector_store.index.ntotal} vectors")
    except Exception as e:
        print(f"[GreenRights] Warning: RAG initialization failed: {e}")
        print("[GreenRights] The app will still work but RAG search will be unavailable")

    # Start session cleanup loop
    await session_store.start_cleanup_loop(interval_minutes=30)
    print(
        f"[GreenRights] Session store ready (TTL: {settings.SESSION_TTL_HOURS}h)")

    print("[GreenRights] Ready to serve requests!")
    yield

    # Shutdown
    print("[GreenRights] Shutting down...")
    session_store.stop_cleanup_loop()


app = FastAPI(
    title="GreenRights API",
    description="AI-powered French green transition entitlement advisor",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — build origins list from config + extra env var
_cors_origins = [
    settings.FRONTEND_URL,
    "http://localhost:3000",
    "http://localhost:3001",
]
if settings.EXTRA_CORS_ORIGINS:
    _cors_origins.extend(
        o.strip() for o in settings.EXTRA_CORS_ORIGINS.split(",") if o.strip()
    )
# Deduplicate while preserving order
_cors_origins = list(dict.fromkeys(_cors_origins))

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(chat.router)
app.include_router(calculate.router)
app.include_router(report.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    from .rag.store import vector_store

    return {
        "status": "healthy",
        "service": "greenrights-api",
        "version": "1.0.0",
        "sessions_active": session_store.get_session_count(),
        "rag_index_ready": vector_store.index is not None,
        "rag_vectors": vector_store.index.ntotal if vector_store.index else 0,
    }


@app.get("/api/demo-profiles")
async def list_demo_profiles():
    """List available demo profiles."""
    import json

    demo_path = settings.DATA_DIR / "demo_profiles.json"
    if not demo_path.exists():
        return {"profiles": {}}

    with open(demo_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Return summary without full profile data
    profiles = {}
    raw = data.get("profiles", [])
    if isinstance(raw, list):
        for profile in raw:
            pid = profile.get("id", profile.get("name", ""))
            profiles[pid] = {
                "name": profile.get("name", pid),
                "description_fr": profile.get("description_fr", ""),
                "description_en": profile.get("description_en", ""),
                "commune": profile.get("commune", ""),
                "income_bracket": profile.get("income_bracket", ""),
            }
    elif isinstance(raw, dict):
        for name, profile in raw.items():
            profiles[name] = {
                "name": profile.get("name", name),
                "description_fr": profile.get("description_fr", ""),
                "description_en": profile.get("description_en", ""),
                "commune": profile.get("commune", ""),
                "income_bracket": profile.get("income_bracket", ""),
            }

    return {"profiles": profiles}
