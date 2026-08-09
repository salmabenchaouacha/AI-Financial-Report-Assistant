import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    UPLOAD_FOLDER = BASE_DIR / "storage" / "pdf"
    RESULTS_FOLDER = BASE_DIR / "storage" / "results"

    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50 Mo max par PDF
    ALLOWED_EXTENSIONS = {"pdf"}

    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    E2B_API_KEY = os.environ.get("E2B_API_KEY", "")

    CHROMA_PERSIST_DIR = BASE_DIR / "storage" / "chroma_db"