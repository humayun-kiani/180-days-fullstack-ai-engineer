# ============================================================
# src/main.py
# Application entry point
# ============================================================

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import uvicorn
from src.api import app


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    debug = os.environ.get("DEBUG", "false").lower() == "true"

    uvicorn.run(
        "src.api:app",
        host="0.0.0.0",    # listen on all interfaces inside container
        port=port,
        reload=debug,      # auto-reload on code changes (dev only)
        log_level="info"
    )