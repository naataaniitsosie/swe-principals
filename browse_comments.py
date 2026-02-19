#!/usr/bin/env python3
"""
Convert preprocessed events from the single SQLite DB to Markdown files per repo,
organized by date. Use for scrolling through comments with full metadata.
"""
import argparse
import json
import sqlite3
from pathlib import Path
from collections import defaultdict
from typing import List

from project_config import DATA_DIR


def _table_for_db(conn: sqlite3.Connection) -> str:
    """Use cleaned if present, else events."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('cleaned','events') ORDER BY name DESC"
    )
    row = cursor.fetchone()
    return row[0] if row else "events"


def _repo_from_record(rec: dict) -> str:
    """Repo name from record (cleaned: top-level repo; raw: repo.name)."""
    repo = rec.get("repo")
    if isinstance(repo, str):
        return repo
    return (repo or {}).get("name") or ""


def load_records_by_repo(db_path: Path) -> dict[str, List[dict]]:
    """Load all records from DB (cleaned or events table), grouped by repo."""
    conn = sqlite3.connect(str(db_path))
    table = _table_for_db(conn)
    cursor = conn.execute(f"SELECT id, event_data FROM {table}")
    rows = [(row[0], row[1]) for row in cursor]
    conn.close()
    # Parse and sort by created_at then id; group by repo
    records = []
    for _id, event_data in rows:
        try:
            rec = json.loads(event_data)
            rec.setdefault("id", _id)
            records.append(rec)
        except (json.JSONDecodeError, TypeError):
            continue
    records.sort(key=lambda r: (r.get("created_at") or "", str(r.get("id") or "")))
    by_repo: dict[str, List[dict]] = defaultdict(list)
    for rec in records:
        by_repo[_repo_from_record(rec)].append(rec)
    return dict(by_repo)


def date_from_created_at(created_at: str) -> str:
    """Return YYYY-MM-DD from ISO created_at."""
    return (created_at or "")[:10] if created_at else ""


def record_to_md(rec: dict, number: int) -> str:
    """Format one record as Markdown: number, metadata block + cleaned text."""
    lines = [
        f"### {number}.",
        "",
        f"- **id:** {rec.get('id', '')}",
        f"- **repo:** {rec.get('repo', '')}",
        f"- **created_at:** {rec.get('created_at', '')}",
        f"- **type:** {rec.get('type', '')}",
        f"- **author_association:** {rec.get('author_association', '')}",
        f"- **tokens:** {rec.get('tokens', [])}",
        "",
        rec.get("cleaned_text") or "",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


def records_to_md(records: List[dict], repo_label: str) -> str:
    """Group records by date, build one Markdown document with outline by date."""
    by_date: dict[str, list[dict]] = defaultdict(list)
    for rec in records:
        d = date_from_created_at(rec.get("created_at") or "")
        if d:
            by_date[d].append(rec)

    parts = [f"# Repo: {repo_label}\n"]
    for date in sorted(by_date.keys()):
        parts.append(f"## {date}\n")
        for i, rec in enumerate(by_date[date], start=1):
            parts.append(record_to_md(rec, i))
    return "\n".join(parts).strip()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Convert preprocessed SQLite DB to one Markdown file per repo, organized by date."
    )
    parser.add_argument(
        "dir",
        type=Path,
        nargs="?",
        default=DATA_DIR,
        help="Directory containing events.db; one .md per repo written here (default: from project_config)",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        metavar="DIR",
        help="Use this directory for events.db instead of dir",
    )
    args = parser.parse_args()

    from dataset_readers.gharchive.storage import DEFAULT_DB_FILENAME
    input_dir = args.dir
    if not input_dir.is_dir():
        raise SystemExit(f"Not a directory: {input_dir}")
    db_dir = args.db if args.db is not None else input_dir
    db_path = db_dir / DEFAULT_DB_FILENAME
    if not db_path.exists():
        raise SystemExit(f"Database not found: {db_path}")

    by_repo = load_records_by_repo(db_path)
    for repo, records in sorted(by_repo.items()):
        if not records:
            continue
        repo_label = repo
        md_content = records_to_md(records, repo_label)
        safe_name = repo.replace("/", "_")
        out_path = input_dir / f"{safe_name}.md"
        out_path.write_text(md_content, encoding="utf-8")
        print(f"Wrote {out_path.name} ({len(records)} comments)")


if __name__ == "__main__":
    main()
