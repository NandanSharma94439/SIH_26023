import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# Base backend directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Load .env file (check both backend/.env and workspace root .env if present)
load_dotenv(BASE_DIR / ".env")
if (BASE_DIR.parent / ".env").exists():
    load_dotenv(BASE_DIR.parent / ".env")


class Settings:
    BASE_DIR: Path = BASE_DIR
    PROJECT_NAME: str = os.getenv("PROJECT_NAME", "Mining Document Intelligence API")
    PROJECT_DESCRIPTION: str = (
        "AI-Powered Geological, Mining and Reporting Solution for CMPDI/CIL subsidiaries "
        "(SIH 2026 - Problem Statement 26023)"
    )
    API_VERSION: str = os.getenv("API_VERSION", "v1")
    ENVIRONMENT: str = os.getenv("ENVIRONMENT", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() in ("true", "1", "yes")

    # Server configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("PORT") or os.getenv("API_PORT", "8000"))

    # CORS configuration
    CORS_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000",
        ).split(",")
        if origin.strip()
    ]

    # Gemini LLM configuration (Backend only)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite")
    GEMINI_EMBEDDING_MODEL: str = os.getenv("GEMINI_EMBEDDING_MODEL", "gemini-embedding-001")

    # RAG Chunking Configuration
    CHUNK_SIZE: int = int(os.getenv("RAG_CHUNK_SIZE", "800"))
    CHUNK_OVERLAP: int = int(os.getenv("RAG_CHUNK_OVERLAP", "150"))

    # Database & Supabase configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./storage/mining_dev.db")
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # Storage paths
    UPLOAD_DIRECTORY: Path = BASE_DIR / os.getenv("UPLOAD_DIRECTORY", "storage/uploads")
    PROCESSED_DIRECTORY: Path = BASE_DIR / os.getenv("PROCESSED_DIRECTORY", "storage/processed")
    FAISS_INDEX_PATH: Path = BASE_DIR / os.getenv("FAISS_INDEX_PATH", "storage/faiss_index/mining_docs.index")
    FAISS_METADATA_PATH: Path = BASE_DIR / os.getenv("FAISS_METADATA_PATH", "storage/faiss_index/mining_docs_metadata.pkl")

    def ensure_directories(self) -> None:
        """Create necessary storage directories if they do not exist."""
        self.UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
        self.PROCESSED_DIRECTORY.mkdir(parents=True, exist_ok=True)
        self.FAISS_INDEX_PATH.parent.mkdir(parents=True, exist_ok=True)


settings = Settings()
settings.ensure_directories()
