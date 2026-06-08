"""
SQLite helpers for the samples table: CREATE TABLE, insert, query.
Schema defined here is the source of truth — update README.md if changed.
"""
import sqlite3
from typing import List, Tuple

SAMPLES_TABLE = "samples"

SAMPLES_SCHEMA = """
CREATE TABLE IF NOT EXISTS samples (
    id          TEXT PRIMARY KEY,
    repo        TEXT NOT NULL,
    event_type  TEXT NOT NULL,
    stratum_key TEXT NOT NULL
)
"""


def create_samples_table(conn: sqlite3.Connection) -> None:
    conn.executescript(SAMPLES_SCHEMA.strip())


def insert_samples(conn: sqlite3.Connection, rows: List[Tuple[str, str, str, str]]) -> None:
    """Insert (id, repo, event_type, stratum_key) rows using INSERT OR REPLACE."""
    conn.executemany(
        "INSERT OR REPLACE INTO samples (id, repo, event_type, stratum_key) VALUES (?, ?, ?, ?)",
        rows,
    )


def query_strata_counts(conn: sqlite3.Connection) -> List[Tuple[str, int]]:
    """Return (stratum_key, count) sorted by stratum_key for logging."""
    cursor = conn.execute(
        "SELECT stratum_key, COUNT(*) FROM samples GROUP BY stratum_key ORDER BY stratum_key"
    )
    return cursor.fetchall()
