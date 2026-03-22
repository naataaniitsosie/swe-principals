"""
Project config: single data directory and one DB file.
All extraction and preprocessing use data/raw/events.db unless overridden here.

Loads `.env` from the repository root when this module is imported so variables like
`OPENAI_API_TOKEN` are available without manual `export` (requires `python-dotenv`).
"""
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent


def _load_dotenv() -> None:
    """Load `.env` from repo root; no-op if python-dotenv is missing."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(_REPO_ROOT / ".env")


_load_dotenv()

# Single directory for raw (and by default cleaned) data. No output-dir option in CLI.
DATA_DIR: Path = Path("data/raw")

# Single SQLite database filename.
DB_FILENAME: str = "events.db"

# Default repo for judge (and other analysis) when filtering by repo. Use owner/repo (e.g. expressjs/express).
JUDGE_DEFAULT_REPO: str = "expressjs/express"


def db_path(base_dir: Path | None = None) -> Path:
    """Path to the events database. Default: DATA_DIR / DB_FILENAME."""
    return (base_dir or DATA_DIR) / DB_FILENAME


def repo_root() -> Path:
    """Absolute path to the repository root (directory containing `project_config.py`)."""
    return _REPO_ROOT
