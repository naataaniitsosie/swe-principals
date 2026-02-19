"""
Storage layer for extracted GHArchive events using a single SQLite database.
One DB per output dir; events table has repo and other indexed columns for querying.
Uses INSERT OR REPLACE for resumable extraction (dedupe by event id).
"""
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Default single-DB filename
DEFAULT_DB_FILENAME = "events.db"

# Indexed columns for querying (in addition to id and event_data).
# Useful attributes for filtering and analytics:
#   repo             - repository (e.g. django/django) for per-repo queries
#   created_at       - ISO timestamp for time range and ordering
#   type             - event type (IssueCommentEvent, PullRequestEvent, etc.)
#   author_association - MEMBER, CONTRIBUTOR, NONE, etc.
#   actor_login      - GitHub login of the actor
EVENTS_TABLE_COLUMNS = [
    "id TEXT PRIMARY KEY",
    "repo TEXT NOT NULL",
    "created_at TEXT",
    "type TEXT",
    "author_association TEXT",
    "actor_login TEXT",
    "event_data TEXT NOT NULL",
]


def _extract_repo(event: Dict[str, Any]) -> str:
    return (event.get("repo") or {}).get("name") or ""


def _extract_created_at(event: Dict[str, Any]) -> str:
    return event.get("created_at") or ""


def _extract_type(event: Dict[str, Any]) -> str:
    return event.get("type") or ""


def _extract_author_association(event: Dict[str, Any]) -> str:
    payload = event.get("payload") or {}
    return (
        payload.get("comment", {}).get("author_association")
        or payload.get("review", {}).get("author_association")
        or payload.get("pull_request", {}).get("author_association")
        or payload.get("issue", {}).get("author_association")
        or ""
    )


def _extract_actor_login(event: Dict[str, Any]) -> str:
    return (event.get("actor") or {}).get("login") or ""


def _create_events_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS events (\n  " + ",\n  ".join(EVENTS_TABLE_COLUMNS) + "\n)"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_repo ON events(repo)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_created_at ON events(created_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_type ON events(type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_author_association ON events(author_association)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_events_actor_login ON events(actor_login)")


def get_raw_db_stats(db_path: Path) -> Dict[str, Any]:
    """Return size and row counts for the raw events DB (for logging after extraction)."""
    if not db_path.exists():
        return {"path": str(db_path), "size_bytes": 0, "total_rows": 0, "by_repo": {}}
    size_bytes = db_path.stat().st_size
    conn = sqlite3.connect(str(db_path))
    (total_rows,) = conn.execute("SELECT COUNT(*) FROM events").fetchone()
    cursor = conn.execute("SELECT repo, COUNT(*) FROM events GROUP BY repo ORDER BY repo")
    by_repo = {row[0]: row[1] for row in cursor}
    conn.close()
    return {
        "path": str(db_path),
        "size_bytes": size_bytes,
        "total_rows": total_rows,
        "by_repo": by_repo,
    }


def _create_cleaned_table(conn: sqlite3.Connection) -> None:
    """Same schema as events; used when preprocess writes to the same DB."""
    conn.execute(
        "CREATE TABLE IF NOT EXISTS cleaned (\n  " + ",\n  ".join(EVENTS_TABLE_COLUMNS) + "\n)"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cleaned_repo ON cleaned(repo)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cleaned_created_at ON cleaned(created_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cleaned_type ON cleaned(type)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cleaned_author_association ON cleaned(author_association)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_cleaned_actor_login ON cleaned(actor_login)")


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
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        (self._initial_count,) = self._conn.execute("SELECT COUNT(*) FROM events").fetchone()
        self._count = 0  # net new rows this run (updated after each batch)

    def append_events(self, events: List[Dict[str, Any]]) -> None:
        """Insert or replace events by id (resumable extraction). Extracts repo, created_at, type, etc. for indexing."""
        (total_before,) = self._conn.execute("SELECT COUNT(*) FROM events").fetchone()
        for event in events:
            eid = str(event.get("id", ""))
            if not eid:
                continue
            repo = _extract_repo(event)
            created_at = _extract_created_at(event)
            etype = _extract_type(event)
            author_association = _extract_author_association(event)
            actor_login = _extract_actor_login(event)
            event_json = json.dumps(event, ensure_ascii=False)
            self._conn.execute(
                """INSERT OR REPLACE INTO events
                   (id, repo, created_at, type, author_association, actor_login, event_data)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (eid, repo, created_at, etype, author_association, actor_login, event_json),
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
        """Write extraction metadata and close connection."""
        meta = {
            "record_count": self._count,
            "saved_at": datetime.now().isoformat(),
            "file_path": str(self._path),
        }
        if additional_metadata:
            meta.update(additional_metadata)
        metadata_json = json.dumps(meta, ensure_ascii=False)
        self._conn.execute(
            "INSERT OR REPLACE INTO metadata (key, value) VALUES (?, ?)",
            ("extraction_metadata", metadata_json),
        )
        self._conn.commit()
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
