import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

DEMO_MODE = os.getenv("DEMO_MODE", "false").strip().lower() in {"1", "true", "yes", "on"}

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{ROOT / 'forenselab.db'}")
STORAGE = Path(os.getenv("STORAGE_DIR", str(ROOT / "storage" / "evidence"))).resolve()

DEFAULT_MAX_UPLOAD = 5 * 1024 * 1024 if DEMO_MODE else 50 * 1024 * 1024
MAX_UPLOAD = int(os.getenv("MAX_UPLOAD_BYTES", str(DEFAULT_MAX_UPLOAD)))

_raw_origins = os.getenv("CORS_ORIGINS", "http://localhost:5173")
CORS_ORIGINS = [origin.strip().rstrip("/") for origin in _raw_origins.split(",") if origin.strip()]
