"""
Storage for judge: read cleaned rows from SQLite, write score rows with deduplication.
Cleaned is normalized (id, cleaned_text, tokens); join with events for repo, created_at, type, author_association.
Filters are applied at DB query time via JOIN + WHERE; extend CLEANED_JOIN_FILTERS to add more.
"""
import json
import sqlite3
from pathlib import Path
from typing import Iterator, List, Optional, Set

from preprocessing.workflow import metadata_from_raw_event

SCORES_TABLE = "scores"
CLEANED_TABLE = "cleaned"
EVENTS_TABLE = "events"

# Base query: cleaned JOIN events so we can filter on raw event_data.
CLEANED_JOIN_SQL = f"""
SELECT c.id, c.cleaned_text, c.tokens, e.event_data
FROM {CLEANED_TABLE} c
INNER JOIN {EVENTS_TABLE} e ON e.id = c.id
"""

# Filter key -> SQL fragment (use ? for placeholders). All conditions are ANDed at query time.
# To add a filter: (1) add key -> fragment here (reference e.event_data via json_extract);
# (2) in _build_cleaned_join_query append one param per ? (or extend for multi-? e.g. author_association);
# (3) pass the key from runner/CLI via the filters dict.
CLEANED_JOIN_FILTERS = {
    "repo": "json_extract(e.event_data, '$.repo.name') = ?",
    "type": "json_extract(e.event_data, '$.type') = ?",
    "author_association": (
        "("
        "json_extract(e.event_data, '$.payload.comment.author_association') = ? OR "
        "json_extract(e.event_data, '$.payload.review.author_association') = ? OR "
        "json_extract(e.event_data, '$.payload.pull_request.author_association') = ? OR "
        "json_extract(e.event_data, '$.payload.issue.author_association') = ?"
        ")"
    ),
}


def _build_cleaned_join_query(filters: dict) -> tuple[str, list]:
    """Build (sql, params) for the cleaned JOIN events query. Filters are ANDed at DB query time."""
    where_parts = []
    params: list = []
    for key, value in filters.items():
        if key not in CLEANED_JOIN_FILTERS:
            continue
        if value is None or (isinstance(value, str) and value.strip() == ""):
            continue
        fragment = CLEANED_JOIN_FILTERS[key]
        where_parts.append(fragment)
        if key == "author_association":
            params.extend([value] * 4)
        else:
            params.append(value)
    sql = CLEANED_JOIN_SQL.strip()
    if where_parts:
        sql += " WHERE " + " AND ".join(where_parts)
    return sql, params

SCORES_SCHEMA = """
CREATE TABLE IF NOT EXISTS scores (
    comment_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    nsi_score INTEGER NOT NULL,
    isi_score INTEGER NOT NULL,
    nsi_reasoning TEXT NOT NULL,
    isi_reasoning TEXT NOT NULL,
    created_at TEXT,
    PRIMARY KEY (comment_id, model_name)
)
"""


class CleanedReader:
    """
    Reads cleaned records by JOIN with events; filters applied at DB query time.
    Pass filters dict (e.g. {"repo": "expressjs/express", "type": "PullRequestReviewCommentEvent"}).
    Add entries to CLEANED_JOIN_FILTERS in this module to support new filter keys.
    """

    def __init__(
        self,
        db_path: Path,
        skip_comment_ids: Optional[Set[str]] = None,
        repo_filter: Optional[str] = None,
        filters: Optional[dict] = None,
    ):
        self._db_path = Path(db_path)
        self._skip_ids = skip_comment_ids or set()
        if filters is not None:
            self._filters = dict(filters)
        elif repo_filter and str(repo_filter).strip():
            self._filters = {"repo": str(repo_filter).strip()}
        else:
            self._filters = {}

    def list_records(self) -> List[dict]:
        """Read cleaned records via JOIN with events; WHERE built from self._filters."""
        if not self._db_path.exists():
            return []
        conn = sqlite3.connect(str(self._db_path))
        try:
            sql, params = _build_cleaned_join_query(self._filters)
            cursor = conn.execute(sql, params)
            records = []
            for row in cursor:
                comment_id, cleaned_text, tokens_str, event_data_str = row[0], row[1], row[2], row[3]
                if comment_id in self._skip_ids:
                    continue
                if not (cleaned_text or "").strip():
                    continue
                try:
                    event_data = json.loads(event_data_str)
                    meta = metadata_from_raw_event(event_data)
                    tokens = json.loads(tokens_str) if tokens_str else []
                    rec = {
                        "id": comment_id,
                        "cleaned_text": cleaned_text,
                        "repo": meta["repo"],
                        "created_at": meta["created_at"],
                        "type": meta["type"],
                        "author_association": meta["author_association"],
                        "tokens": tokens,
                    }
                    records.append(rec)
                except (json.JSONDecodeError, TypeError):
                    continue
            return records
        finally:
            conn.close()

    def iter_records(self) -> Iterator[dict]:
        """Yield cleaned records (id, cleaned_text, ...). Connection is closed before first yield."""
        yield from self.list_records()


class ScoresWriter:
    """
    Creates the scores table if needed and writes score rows.
    Uses INSERT OR REPLACE so (comment_id, model_name) is deduplicated.
    """

    def __init__(self, db_path: Path):
        self._db_path = Path(db_path)
        self._ensure_table()

    def _ensure_table(self) -> None:
        conn = sqlite3.connect(str(self._db_path))
        conn.executescript(SCORES_SCHEMA)
        conn.commit()
        conn.close()

    def write(
        self,
        comment_id: str,
        model_name: str,
        nsi_score: int,
        isi_score: int,
        nsi_reasoning: str,
        isi_reasoning: str,
        created_at: Optional[str] = None,
    ) -> None:
        """Write one score row (insert or replace)."""
        conn = sqlite3.connect(str(self._db_path))
        conn.execute(
            """
            INSERT OR REPLACE INTO scores
            (comment_id, model_name, nsi_score, isi_score, nsi_reasoning, isi_reasoning, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                comment_id,
                model_name,
                nsi_score,
                isi_score,
                nsi_reasoning or "",
                isi_reasoning or "",
                created_at,
            ),
        )
        conn.commit()
        conn.close()

    def write_batch(
        self,
        rows: list[tuple[str, str, int, int, str, str, Optional[str]]],
    ) -> None:
        """Write multiple score rows. Each tuple: (comment_id, model_name, nsi_score, isi_score, nsi_reasoning, isi_reasoning, created_at)."""
        if not rows:
            return
        conn = sqlite3.connect(str(self._db_path))
        conn.executemany(
            """
            INSERT OR REPLACE INTO scores
            (comment_id, model_name, nsi_score, isi_score, nsi_reasoning, isi_reasoning, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
        conn.close()


def get_scored_comment_ids(db_path: Path, model_name: str) -> Set[str]:
    """Return set of comment_id already scored for the given model (for skip-existing)."""
    db_path = Path(db_path)
    if not db_path.exists():
        return set()
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.execute(
            "SELECT comment_id FROM scores WHERE model_name = ?",
            (model_name,),
        )
        return {row[0] for row in cursor}
    finally:
        conn.close()
