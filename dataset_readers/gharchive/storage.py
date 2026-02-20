"""
Storage layer for extracted GHArchive events using a single SQLite database.
One DB file per output dir (default: data/raw/events.db). Uses INSERT OR REPLACE
for resumable extraction (dedupe by event id).

Tables
------
events
    Raw events from extraction (dataset.py). Columns: id (PK), event_data (JSON blob).
    event_data is the full GitHub event; query with json_extract(event_data, '$....').

cleaned
    Preprocessed events (preprocess.py). Same schema: id (PK), event_data (JSON blob).
    event_data JSON fields: id, cleaned_text, repo, created_at, type, author_association, tokens.
    Created only when preprocessing writes to the same DB.
"""
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

DEFAULT_DB_FILENAME = "events.db"

# Single schema: id + JSON blob. Used for both events and cleaned tables.
EVENTS_TABLE_COLUMNS = [
    "id TEXT PRIMARY KEY",
    "event_data TEXT NOT NULL",
]


def _create_events_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS events (\n  " + ",\n  ".join(EVENTS_TABLE_COLUMNS) + "\n)"
    )


def _repo_from_event_data(event_data: str) -> str:
    """Extract repo name from event_data JSON (raw: $.repo.name, cleaned: $.repo)."""
    try:
        obj = json.loads(event_data)
        repo = obj.get("repo")
        if isinstance(repo, str):
            return repo
        return (repo or {}).get("name") or ""
    except (json.JSONDecodeError, TypeError):
        return ""


def get_raw_db_stats(db_path: Path) -> Dict[str, Any]:
    """Return size and row counts for the raw events DB (for logging after extraction)."""
    if not db_path.exists():
        return {"path": str(db_path), "size_bytes": 0, "total_rows": 0, "by_repo": {}}
    size_bytes = db_path.stat().st_size
    conn = sqlite3.connect(str(db_path))
    (total_rows,) = conn.execute("SELECT COUNT(*) FROM events").fetchone()
    cursor = conn.execute("SELECT event_data FROM events")
    by_repo: Dict[str, int] = {}
    for (blob,) in cursor:
        repo = _repo_from_event_data(blob) or "(no repo)"
        by_repo[repo] = by_repo.get(repo, 0) + 1
    conn.close()
    by_repo = dict(sorted(by_repo.items()))
    return {
        "path": str(db_path),
        "size_bytes": size_bytes,
        "total_rows": total_rows,
        "by_repo": by_repo,
    }


def _create_cleaned_table(conn: sqlite3.Connection) -> None:
    """Same schema as events: id + event_data. Used when preprocess writes to the same DB."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS cleaned (\n  " + ",\n  ".join(EVENTS_TABLE_COLUMNS) + "\n)"
    )


class StreamingWriter:
    """
    Writes events to a single SQLite database. All repos append to the same DB.
    Uses INSERT OR REPLACE for resumable extraction (dedupe by event id).
    Call append_events() per batch, then finalize() once when done.
    """

    def __init__(self, db_path: Path):
        self._path = db_path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self._path))
        _create_events_table(self._conn)
        (self._initial_count,) = self._conn.execute("SELECT COUNT(*) FROM events").fetchone()
        self._count = 0  # net new rows this run (updated after each batch)

    def append_events(self, events: List[Dict[str, Any]]) -> None:
        """Insert or replace events by id (resumable extraction). Stores full event as JSON."""
        (total_before,) = self._conn.execute("SELECT COUNT(*) FROM events").fetchone()
        for event in events:
            eid = str(event.get("id", ""))
            if not eid:
                continue
            event_json = json.dumps(event, ensure_ascii=False)
            self._conn.execute(
                "INSERT OR REPLACE INTO events (id, event_data) VALUES (?, ?)",
                (eid, event_json),
            )
        self._conn.commit()
        (total_after,) = self._conn.execute("SELECT COUNT(*) FROM events").fetchone()
        net_this_batch = total_after - total_before
        self._count = total_after - self._initial_count
        size_bytes = self._path.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        logger.info(
            "DB: %.2f MiB | total rows: %d | added this batch: %d | added this run: %d",
            size_mb,
            total_after,
            net_this_batch,
            self._count,
        )

    def finalize(self, additional_metadata: Optional[Dict[str, Any]] = None) -> str:
        """Close connection. additional_metadata is ignored (no metadata table)."""
        self._conn.close()
        logger.info("Saved %s new records (net) to %s", self._count, self._path)
        return str(self._path)

    @property
    def path(self) -> Path:
        return self._path

    @property
    def count(self) -> int:
        return self._count


class SQLiteStorage:
    """Single SQLite database per output directory; events have repo and other indexed columns."""

    def __init__(self, base_dir: str, db_filename: str = DEFAULT_DB_FILENAME):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.db_filename = db_filename
        self._db_path = self.base_dir / self.db_filename

    def create_writer(self) -> StreamingWriter:
        """Create a single streaming writer for the shared DB. Append events from any repo; call finalize() once when done."""
        return StreamingWriter(self._db_path)


class DataRepository:
    """Thin wrapper over SQLiteStorage for extraction writer."""

    def __init__(self, storage: SQLiteStorage):
        self.storage = storage

    def create_extraction_writer(self) -> StreamingWriter:
        return self.storage.create_writer()
