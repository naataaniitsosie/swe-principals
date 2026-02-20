#!/usr/bin/env python3
"""
Migrate GitHub event JSONL files into the project SQLite DB (events table).
Reuses project_config for DB path and storage._create_events_table for schema.
Does not modify any existing code. Usage:

  python migrate_jsonl_to_db.py file1.jsonl file2.jsonl ...
  python migrate_jsonl_to_db.py data/raw/2024/*.jsonl
"""
import argparse
import json
import sqlite3
import sys
from pathlib import Path

from project_config import db_path
from dataset_readers.gharchive.storage import _create_events_table


def ingest_jsonl_into_db(jsonl_paths: list[Path], db_path_val: Path) -> tuple[int, int]:
    """Read each JSONL file, INSERT OR REPLACE into events. Returns (lines_read, rows_written)."""
    db_path_val.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path_val))
    _create_events_table(conn)

    total_read = 0
    total_written = 0
    for path in jsonl_paths:
        if not path.is_file():
            print(f"Skip (not a file): {path}", file=sys.stderr)
            continue
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                total_read += 1
                try:
                    event = json.loads(line)
                except json.JSONDecodeError:
                    continue
                eid = event.get("id")
                if eid is None:
                    continue
                eid_str = str(eid)
                event_json = json.dumps(event, ensure_ascii=False)
                conn.execute(
                    "INSERT OR REPLACE INTO events (id, event_data) VALUES (?, ?)",
                    (eid_str, event_json),
                )
                total_written += 1
        conn.commit()
    conn.close()
    return total_read, total_written


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Migrate GitHub event JSONL files into the project DB (events table)."
    )
    parser.add_argument(
        "jsonl_files",
        type=Path,
        nargs="+",
        help="Paths to .jsonl files (one JSON object per line).",
    )
    args = parser.parse_args()

    target = db_path()
    read, written = ingest_jsonl_into_db(args.jsonl_files, target)
    print(f"Read {read} lines, wrote {written} rows to {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
