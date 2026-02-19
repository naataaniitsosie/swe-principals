"""
Pipeline to clean dataset_reader output (CONFORMITY.md Preprocessing).
Reads only from the single SQLite DB (events table); no JSONL. Writes cleaned events to the same DB
(cleaned table) or another DB. Preserves repo, created_at, type, author_association for querying.
"""
import json
import sqlite3
import logging
from pathlib import Path
from typing import List, Optional

from preprocessing.workflow import Workflow, default_workflow
from dataset_readers.gharchive.storage import (
    DEFAULT_DB_FILENAME,
    _create_events_table,
    _create_cleaned_table,
)

logger = logging.getLogger(__name__)


def clean_db(
    workflow: Workflow,
    input_path: Path,
    output_path: Path,
) -> tuple[int, int, int]:
    """Read from input_path (events table), run workflow, write to output_path. If same path, write to cleaned table; else write to events in new db. Returns (read_count, duplicate_count, written_count)."""
    read_count = 0
    duplicate_count = 0
    written_count = 0
    seen_ids = set()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    same_db = input_path.resolve() == output_path.resolve()
    input_conn = sqlite3.connect(str(input_path))
    input_cursor = input_conn.execute("SELECT event_data FROM events")

    if same_db:
        output_conn = input_conn
        _create_cleaned_table(output_conn)
        out_table = "cleaned"
    else:
        output_conn = sqlite3.connect(str(output_path))
        _create_events_table(output_conn)
        output_conn.execute("""
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            )
        """)
        out_table = "events"

    for row in input_cursor:
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
            repo = cleaned.get("repo") or ""
            created_at = cleaned.get("created_at") or ""
            etype = cleaned.get("type") or ""
            author_association = cleaned.get("author_association") or ""
            actor_login = ""
            cleaned_json = json.dumps(cleaned, ensure_ascii=False)
            output_conn.execute(
                f"""INSERT OR REPLACE INTO {out_table}
                   (id, repo, created_at, type, author_association, actor_login, event_data)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (eid_key or str(read_count), repo, created_at, etype, author_association, actor_login, cleaned_json),
            )
            written_count += 1

    output_conn.commit()
    output_conn.close()
    if not same_db:
        input_conn.close()
    return read_count, duplicate_count, written_count


class CleanerPipeline:
    """Run a preprocessing workflow on the single SQLite database in input_dir (events.db), write to output_dir/events.db."""

    def __init__(self, input_dir: str, output_dir: str, workflow: Optional[Workflow] = None):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.workflow = workflow if workflow is not None else default_workflow()

    def run(self) -> List[tuple[str, int, int, int]]:
        """
        Read events.db from input_dir, dedupe by id, run workflow, write to output_dir/events.db.
        Returns list of (filename, read_count, duplicate_count, written_count); single element for events.db.
        """
        results = []
        input_path = self.input_dir / DEFAULT_DB_FILENAME
        if not input_path.exists():
            logger.warning("No %s found in %s", DEFAULT_DB_FILENAME, self.input_dir)
            return results
        output_path = self.output_dir / DEFAULT_DB_FILENAME
        read_count, duplicate_count, written_count = clean_db(self.workflow, input_path, output_path)
        results.append((DEFAULT_DB_FILENAME, read_count, duplicate_count, written_count))
        logger.info(
            "%s: read %s, duplicates %s, kept %s",
            DEFAULT_DB_FILENAME,
            read_count,
            duplicate_count,
            written_count,
        )
        return results
