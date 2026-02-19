"""
Pipeline to clean dataset_reader output (CONFORMITY.md Preprocessing).
Reads from the single SQLite DB (events table: id + event_data), writes cleaned table to same DB.
DB path is from project config (preprocess.py passes DATA_DIR).
"""
import json
import sqlite3
import logging
from pathlib import Path
from typing import List, Optional

from preprocessing.workflow import Workflow, default_workflow
from dataset_readers.gharchive.storage import DEFAULT_DB_FILENAME, _create_cleaned_table

logger = logging.getLogger(__name__)


def clean_db(workflow: Workflow, db_path: Path) -> tuple[int, int, int]:
    """Read from db_path (events table), run workflow, write cleaned table to same DB. Returns (read_count, duplicate_count, written_count)."""
    read_count = 0
    duplicate_count = 0
    written_count = 0
    seen_ids = set()
    db_path.parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(str(db_path))
    _create_cleaned_table(conn)
    cursor = conn.execute("SELECT event_data FROM events")

    for row in cursor:
        read_count += 1
        try:
            event = json.loads(row[0])
        except (json.JSONDecodeError, TypeError):
            continue

        eid = event.get("id")
        eid_key = str(eid) if eid is not None else ""
        if eid_key and eid_key in seen_ids:
            duplicate_count += 1
            continue
        if eid_key:
            seen_ids.add(eid_key)

        cleaned = workflow.run(event)
        if cleaned is not None:
            cleaned_json = json.dumps(cleaned, ensure_ascii=False)
            conn.execute(
                "INSERT OR REPLACE INTO cleaned (id, event_data) VALUES (?, ?)",
                (eid_key or str(read_count), cleaned_json),
            )
            written_count += 1

    conn.commit()
    conn.close()
    return read_count, duplicate_count, written_count


class CleanerPipeline:
    """Run preprocessing on the SQLite DB in data_dir (events.db); writes cleaned table to same DB."""

    def __init__(self, data_dir: str, workflow: Optional[Workflow] = None):
        self.data_dir = Path(data_dir)
        self.workflow = workflow if workflow is not None else default_workflow()

    def run(self) -> List[tuple[str, int, int, int]]:
        """Read events from data_dir/events.db, run workflow, write cleaned table. Returns list of (filename, read_count, duplicate_count, written_count)."""
        results = []
        db_path = self.data_dir / DEFAULT_DB_FILENAME
        if not db_path.exists():
            logger.warning("No %s found in %s", DEFAULT_DB_FILENAME, self.data_dir)
            return results
        read_count, duplicate_count, written_count = clean_db(self.workflow, db_path)
        results.append((DEFAULT_DB_FILENAME, read_count, duplicate_count, written_count))
        logger.info(
            "%s: read %s, duplicates %s, kept %s",
            DEFAULT_DB_FILENAME,
            read_count,
            duplicate_count,
            written_count,
        )
        return results
