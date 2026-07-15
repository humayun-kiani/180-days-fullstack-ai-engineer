# ============================================================
# src/config.py
# Configuration module — loads settings from environment
# ============================================================

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file from the project root
# __file__ is this file's path
# .parent goes up one level (to src/)
# .parent again goes up to project root
ROOT_DIR = Path(__file__).parent.parent
ENV_FILE = ROOT_DIR / ".env"

load_dotenv(ENV_FILE)

# Application settings
APP_NAME = os.environ.get("APP_NAME", "Python Toolkit")
VERSION = os.environ.get("VERSION", "1.0.0")
DEBUG = os.environ.get("DEBUG", "False").lower() == "true"
AUTHOR = os.environ.get("AUTHOR", "Unknown")

# Directory paths
DATA_DIR = ROOT_DIR / "data"
SRC_DIR = ROOT_DIR / "src"

# Ensure data directory exists
DATA_DIR.mkdir(exist_ok=True)


def get_config():
    """Return all configuration as a dictionary."""
    return {
        "app_name": APP_NAME,
        "version": VERSION,
        "debug": DEBUG,
        "author": AUTHOR,
        "data_dir": str(DATA_DIR),
        "root_dir": str(ROOT_DIR)
    }


if __name__ == "__main__":
    # Test configuration loading
    config = get_config()
    for key, value in config.items():
        print(f"  {key}: {value}")