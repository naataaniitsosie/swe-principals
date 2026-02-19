"""
Project config: single data directory and one DB file.
All extraction and preprocessing use data/raw/events.db unless overridden here.
"""
from pathlib import Path

# Single directory for raw (and by default cleaned) data. No output-dir option in CLI.
DATA_DIR: Path = Path("data/raw")

# Single SQLite database filename.
DB_FILENAME: str = "events.db"


def db_path(base_dir: Path | None = None) -> Path:
    """Path to the events database. Default: DATA_DIR / DB_FILENAME."""
    return (base_dir or DATA_DIR) / DB_FILENAME
