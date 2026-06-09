"""
Shared judge storage: write score rows and query existing scored IDs.

The scores table stores the full CONFORMITY LLM schema: FUN, NSI, INSI, ISI
(reasoning + 0–3 scores, or -1 when model output could not be parsed).
"""

import sqlite3
from pathlib import Path
from typing import List, Set

SCORES_TABLE = "scores"

# Bump this to start a new experiment run. experiment_version is part of the
# primary key, so bumping it creates a fresh scoring namespace without touching
# any existing rows. Do NOT drop the scores table — it is the permanent record.
EXPERIMENT_VERSION = 1

SCORES_SCHEMA = f"""
CREATE TABLE IF NOT EXISTS scores (
    comment_id         TEXT    NOT NULL,
    model_name         TEXT    NOT NULL,
    experiment_version INTEGER NOT NULL DEFAULT {EXPERIMENT_VERSION},
    fun_score          INTEGER NOT NULL,
    fun_reasoning      TEXT    NOT NULL,
    nsi_score          INTEGER NOT NULL,
    nsi_reasoning      TEXT    NOT NULL,
    insi_score         INTEGER NOT NULL,
    insi_reasoning     TEXT    NOT NULL,
    isi_score          INTEGER NOT NULL,
    isi_reasoning      TEXT    NOT NULL,
    created_at         TEXT,
    parse_ok           INTEGER NOT NULL DEFAULT 1,
    error_type         TEXT    NOT NULL DEFAULT '',
    error_message      TEXT    NOT NULL DEFAULT '',
    raw_response       TEXT    NOT NULL DEFAULT '',
    PRIMARY KEY (comment_id, model_name, experiment_version)
)
"""

_INSERT_SQL = """
INSERT OR REPLACE INTO scores
(comment_id, model_name, experiment_version,
 fun_score, fun_reasoning,
 nsi_score, nsi_reasoning,
 insi_score, insi_reasoning,
 isi_score, isi_reasoning,
 created_at, parse_ok, error_type, error_message, raw_response)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""


def _init_scores_table(conn: sqlite3.Connection) -> None:
    conn.executescript(SCORES_SCHEMA)


class ScoresWriter:
    """
    Creates the scores table if needed and writes score rows.
    Uses INSERT OR REPLACE so (comment_id, model_name) is deduplicated.
    """

    def __init__(self, db_path: Path):
        self._db_path = Path(db_path)
        conn = sqlite3.connect(str(self._db_path))
        try:
            _init_scores_table(conn)
            conn.commit()
        finally:
            conn.close()

    def write_batch(self, rows: List) -> None:
        """Write multiple score rows. Each item must match JudgeResult.to_row() order."""
        if not rows:
            return
        conn = sqlite3.connect(str(self._db_path))
        try:
            conn.executemany(_INSERT_SQL, rows)
            conn.commit()
        finally:
            conn.close()


def get_scored_comment_ids(db_path: Path, model_name: str) -> Set[str]:
    """
    Return successfully scored comment IDs for (model_name, EXPERIMENT_VERSION).
    Used by --skip-existing to resume within the current experiment only.
    """
    db_path = Path(db_path)
    if not db_path.exists():
        return set()
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.execute(
            "SELECT comment_id FROM scores WHERE model_name = ? AND experiment_version = ? AND parse_ok = 1",
            (model_name, EXPERIMENT_VERSION),
        )
        return {row[0] for row in cursor}
    except sqlite3.OperationalError:
        return set()
    finally:
        conn.close()
