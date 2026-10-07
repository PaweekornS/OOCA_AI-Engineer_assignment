"""Application configuration and settings."""

from pathlib import Path
from typing import Optional
import os
from dotenv import load_dotenv

# Load .env if present
load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
KB_DIR = DATA_DIR / "kb"
SAMPLE_TICKETS_PATH = DATA_DIR / "sample_tickets.json"


class Settings:
    """Runtime configuration settings."""

    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")
    openai_model_name: str = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
    openai_temperature: float = float(os.getenv("OPENAI_TEMPERATURE", "0.0"))
    max_tool_calls: int = int(os.getenv("MAX_TOOL_CALLS", "3"))
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Paths
    base_dir: Path = BASE_DIR
    data_dir: Path = DATA_DIR
    kb_dir: Path = KB_DIR
    sample_tickets_path: Path = SAMPLE_TICKETS_PATH


settings = Settings()
