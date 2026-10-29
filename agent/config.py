"""Configuration: model and paths. Reads .env if present."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    # dotenv is optional; env vars can be set directly.
    pass

# The model to use. Set MODEL in .env to whatever your account can call.
MODEL = os.getenv("MODEL", "claude-haiku-5-5")

# Max tokens for each reply.
MAX_TOKENS = 1024

# Project paths.
ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT / "knowledge"
CALENDAR_PATH = ROOT / "data" / "calendar.json"
