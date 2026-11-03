import os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
DATABASE_URL=os.getenv("DATABASE_URL",f"sqlite:///{ROOT/'forenselab.db'}")
STORAGE=Path(os.getenv("STORAGE_DIR",str(ROOT/"storage"/"evidence"))).resolve()
MAX_UPLOAD=int(os.getenv("MAX_UPLOAD_BYTES","52428800"))
