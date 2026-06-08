"""
Storage for judge: read cleaned rows from SQLite, write score rows with deduplication.
Filters are applied at DB query time via WHERE on materialized columns; extend CLEANED_JOIN_FILTERS to add more.

Scores table stores the full CONFORMITY LLM schema: FUN, NSI, INSI, ISI
(reasoning + 0–3 scores, or -1 when model output could not be parsed).
"""
import json
import sqlite3
from pathlib import Path
from typing import Iterator, List, Optional, Set

SCORES_TABLE = "scores"
CLEANED_TABLE = "cleaned"

# Base query: read directly from cleaned (no events JOIN needed; fields are materialized).
CLEANED_JOIN_SQL = f"""
SELECT c.id, c.cleaned_text, c.tokens, c.repo, c.event_type, c.created_at, c.author_association
FROM {CLEANED_TABLE} c
"""

# Filter key -> SQL fragment (use ? for placeholders). All conditions are ANDed at query time.
CLEANED_JOIN_FILTERS = {
    "repo": "c.repo = ?",
    "type": "c.event_type = ?",
    "author_association": "c.author_association = ?",
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
        params.append(value)
    sql = CLEANED_JOIN_SQL.strip()
    if where_parts:
        sql += " WHERE " + " AND ".join(where_parts)
    return sql, params


# Full CONFORMITY LLM output (papers/publication1/CONFORMITY_SYSTEM_PROMPT.md).
SCORES_SCHEMA = """
CREATE TABLE IF NOT EXISTS scores (
    comment_id TEXT NOT NULL,
    model_name TEXT NOT NULL,
    fun_score INTEGER NOT NULL,
    fun_reasoning TEXT NOT NULL,
    nsi_score INTEGER NOT NULL,
    nsi_reasoning TEXT NOT NULL,
    insi_score INTEGER NOT NULL,
    insi_reasoning TEXT NOT NULL,
    isi_score INTEGER NOT NULL,
    isi_reasoning TEXT NOT NULL,
    created_at TEXT,
    parse_ok INTEGER NOT NULL DEFAULT 1,
    error_type TEXT NOT NULL DEFAULT '',
    error_message TEXT NOT NULL DEFAULT '',
    raw_response TEXT NOT NULL DEFAULT '',
    PRIMARY KEY (comment_id, model_name)
)
"""

SCORES_SCHEMA_COLUMNS = {
    "parse_ok": "INTEGER NOT NULL DEFAULT 1",
    "error_type": "TEXT NOT NULL DEFAULT ''",
    "error_message": "TEXT NOT NULL DEFAULT ''",
    "raw_response": "TEXT NOT NULL DEFAULT ''",
}


def _table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table_name})")}


def _ensure_scores_schema(conn: sqlite3.Connection) -> None:
    """Create scores table and add parse metadata columns for older DBs."""
    conn.executescript(SCORES_SCHEMA)
    existing_columns = _table_columns(conn, SCORES_TABLE)
    for column_name, column_def in SCORES_SCHEMA_COLUMNS.items():
        if column_name not in existing_columns:
            conn.execute(f"ALTER TABLE {SCORES_TABLE} ADD COLUMN {column_name} {column_def}")


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
        """Read cleaned records; WHERE built from self._filters."""
        if not self._db_path.exists():
            return []
        conn = sqlite3.connect(str(self._db_path))
        try:
            sql, params = _build_cleaned_join_query(self._filters)
            cursor = conn.execute(sql, params)
            records = []
            for row in cursor:
                comment_id, cleaned_text, tokens_str, repo, event_type, created_at, author_association = row
                if comment_id in self._skip_ids:
                    continue
                if not (cleaned_text or "").strip():
                    continue
                try:
                    tokens = json.loads(tokens_str) if tokens_str else []
                except (json.JSONDecodeError, TypeError):
                    tokens = []
                records.append({
                    "id": comment_id,
                    "cleaned_text": cleaned_text,
                    "repo": repo or "",
                    "created_at": created_at or "",
                    "type": event_type or "",
                    "author_association": author_association or "",
                    "tokens": tokens,
                })
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
        try:
            _ensure_scores_schema(conn)
            conn.commit()
        finally:
            conn.close()

    def write(
        self,
        comment_id: str,
        model_name: str,
        fun_score: int,
        fun_reasoning: str,
        nsi_score: int,
        nsi_reasoning: str,
        insi_score: int,
        insi_reasoning: str,
        isi_score: int,
        isi_reasoning: str,
        created_at: Optional[str] = None,
        parse_ok: int = 1,
        error_type: str = "",
        error_message: str = "",
        raw_response: str = "",
    ) -> None:
        """Write one score row (insert or replace)."""
        conn = sqlite3.connect(str(self._db_path))
        conn.execute(
            """
            INSERT OR REPLACE INTO scores
            (comment_id, model_name, fun_score, fun_reasoning, nsi_score, nsi_reasoning,
             insi_score, insi_reasoning, isi_score, isi_reasoning, created_at,
             parse_ok, error_type, error_message, raw_response)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                comment_id,
                model_name,
                fun_score,
                fun_reasoning or "",
                nsi_score,
                nsi_reasoning or "",
                insi_score,
                insi_reasoning or "",
                isi_score,
                isi_reasoning or "",
                created_at,
                1 if parse_ok else 0,
                error_type or "",
                error_message or "",
                raw_response or "",
            ),
        )
        conn.commit()
        conn.close()

    def write_batch(
        self,
        rows: list[
            tuple[
                str,
                str,
                int,
                str,
                int,
                str,
                int,
                str,
                int,
                str,
                Optional[str],
                int,
                str,
                str,
                str,
            ]
        ],
    ) -> None:
        """Write multiple score rows. Each tuple matches JudgeResult.to_row order."""
        if not rows:
            return
        conn = sqlite3.connect(str(self._db_path))
        conn.executemany(
            """
            INSERT OR REPLACE INTO scores
            (comment_id, model_name, fun_score, fun_reasoning, nsi_score, nsi_reasoning,
             insi_score, insi_reasoning, isi_score, isi_reasoning, created_at,
             parse_ok, error_type, error_message, raw_response)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        conn.commit()
        conn.close()


def get_scored_comment_ids(db_path: Path, model_name: str) -> Set[str]:
    """Return successfully scored comment ids for a model (for skip-existing)."""
    db_path = Path(db_path)
    if not db_path.exists():
        return set()
    conn = sqlite3.connect(str(db_path))
    try:
        columns = _table_columns(conn, SCORES_TABLE)
        if not columns:
            return set()
        if "parse_ok" in columns:
            cursor = conn.execute(
                "SELECT comment_id FROM scores WHERE model_name = ? AND parse_ok = 1",
                (model_name,),
            )
            return {row[0] for row in cursor}
        cursor = conn.execute(
            "SELECT comment_id FROM scores WHERE model_name = ?",
            (model_name,),
        )
        return {row[0] for row in cursor}
    finally:
        conn.close()
