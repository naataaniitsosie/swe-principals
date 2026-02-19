#!/usr/bin/env python3
"""
Stats about the data from the dataset (output of dataset.py).
Chainable after dataset.py: reads the single SQLite DB and reports per-repo
total records, unique by event id, and duplicate count.
"""
import argparse
import sqlite3
from pathlib import Path
from typing import List, Tuple

from project_config import DATA_DIR


def _table_for_db(conn: sqlite3.Connection) -> str:
    """Use cleaned if present, else events."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('cleaned','events') ORDER BY name DESC"
    )
    row = cursor.fetchone()
    return row[0] if row else "events"


def stats_from_db(db_path: Path) -> List[Tuple[str, int, int, int]]:
    """Return list of (repo, total, unique, duplicates) from events or cleaned table."""
    if not db_path.exists():
        return []
    conn = sqlite3.connect(str(db_path))
    table = _table_for_db(conn)
    cursor = conn.execute(
        f"""
        SELECT repo,
               COUNT(*) AS total,
               COUNT(DISTINCT id) AS unique_ids
        FROM {table}
        GROUP BY repo
        ORDER BY repo
    """
    )
    rows = []
    for row in cursor:
        repo, total, unique = row[0], row[1], row[2]
        duplicates = total - unique
        rows.append((repo, total, unique, duplicates))
    conn.close()
    return rows


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Report stats about dataset output: total, unique by id, and duplicate counts per repo. Chainable after dataset.py.",
    )
    parser.add_argument(
        "dir",
        type=Path,
        nargs="?",
        default=DATA_DIR,
        help="Directory containing events.db (default: from project_config)",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        metavar="DIR",
        help="Use this directory for events.db instead of dir (default: dir)",
    )
    parser.add_argument(
        "--no-header",
        action="store_true",
        help="Omit the header row.",
    )
    args = parser.parse_args()
    d = args.dir
    db_dir = args.db if args.db is not None else d
    db_path = db_dir / "events.db"

    if not db_path.exists():
        raise SystemExit(f"Database not found: {db_path}")

    rows = stats_from_db(db_path)
    if not args.no_header:
        print("repo\ttotal\tunique\tduplicates")
    for repo, total, unique, dup in rows:
        print(f"{repo}\t{total}\t{unique}\t{dup}")

    if rows:
        total_all = sum(r[1] for r in rows)
        unique_all = sum(r[2] for r in rows)
        dup_all = sum(r[3] for r in rows)
        if not args.no_header:
            print("-\t-\t-\t-")
            print(f"total\t{total_all}\t{unique_all}\t{dup_all}")


if __name__ == "__main__":
    main()
