"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    # Mistral AI
    MISTRAL_API_KEY: str
    MISTRAL_MODEL: str = "mistral-large-latest"
    MISTRAL_EMBED_MODEL: str = "mistral-embed"

    # Server
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    FRONTEND_URL: str = "http://localhost:3000"

    # Extra CORS origins (comma-separated), e.g. "https://my-app.netlify.app,https://other.com"
    EXTRA_CORS_ORIGINS: str = ""

    # Paths
    DATA_DIR: Path = Path(__file__).parent / "data"
    FAISS_INDEX_PATH: Path = Path(__file__).parent / "data" / "faiss_index.bin"
    CHUNKS_META_PATH: Path = Path(
        __file__).parent / "data" / "chunks_meta.json"
    ANAH_PDF_PATH: Path = Path(__file__).parent / \
        "data" / "anah_guide_2026.pdf"

    # RAG
    RAG_CHUNK_SIZE: int = 1200
    RAG_CHUNK_OVERLAP: int = 100
    RAG_TOP_K: int = 5

    # Session
    SESSION_TTL_HOURS: int = 24

    model_config = {
        # Look for .env in several places (local dev: project root; Docker: /app)
        "env_file": [
            str(Path(__file__).parent.parent / ".env"),       # backend/.env
            # project root .env
            str(Path(__file__).parent.parent.parent / ".env"),
        ],
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
