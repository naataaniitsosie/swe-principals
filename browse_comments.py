#!/usr/bin/env python3
"""
Convert preprocessed events from the SQLite DB to Markdown files per repo, organized by date.
Uses normalized cleaned table: JOIN with events for metadata. Output is always fresh (overwrites and removes stale files).
"""
import json
import sqlite3
from pathlib import Path
from collections import defaultdict
from typing import List

from project_config import DATA_DIR, db_path
from preprocessing.workflow import metadata_from_raw_event


def _repo_from_record(rec: dict) -> str:
    """Repo name from record."""
    repo = rec.get("repo")
    if isinstance(repo, str):
        return repo
    return (repo or {}).get("name") or ""


def load_records_by_repo(db_path: Path) -> dict[str, List[dict]]:
    """Load records from cleaned JOIN events (normalized schema)."""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.execute(
        """SELECT c.id, c.cleaned_text, c.tokens, e.event_data
           FROM cleaned c
           INNER JOIN events e ON e.id = c.id"""
    )
    rows = list(cursor)
    conn.close()
    records = []
    for _id, cleaned_text, tokens_str, event_data_str in rows:
        try:
            event_data = json.loads(event_data_str)
            meta = metadata_from_raw_event(event_data)
            tokens = json.loads(tokens_str) if tokens_str else []
            rec = {
                "id": _id,
                "cleaned_text": cleaned_text or "",
                "repo": meta["repo"],
                "created_at": meta["created_at"],
                "type": meta["type"],
                "author_association": meta["author_association"],
                "tokens": tokens,
            }
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
    """Format one record as Markdown: number, metadata block, cleaned_text, tokens."""
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
        "**cleaned_text:**",
        rec.get("cleaned_text") or "(empty)",
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

    parts = [
        f"# Repo: {repo_label}\n",
        f"**Total:** {len(records)}\n",
    ]
    for date in sorted(by_date.keys()):
        parts.append(f"## {date}\n")
        for i, rec in enumerate(by_date[date], start=1):
            parts.append(record_to_md(rec, i))
    return "\n".join(parts).strip()


def main() -> None:
    path_to_db = db_path()
    data_dir = Path(DATA_DIR)
    if not data_dir.is_dir():
        raise SystemExit(f"Data directory does not exist: {data_dir} (set DATA_DIR in project_config.py)")
    if not path_to_db.exists():
        raise SystemExit(f"Database not found: {path_to_db}")

    # Delete existing repo Markdown files first so output is exactly this run's result.
    for path in data_dir.glob("*.md"):
        path.unlink()
        print(f"Removed {path.name}")

    by_repo = load_records_by_repo(path_to_db)
    for repo, records in sorted(by_repo.items()):
        if not records:
            continue
        md_content = records_to_md(records, repo)
        safe_name = repo.replace("/", "_")
        out_path = data_dir / f"{safe_name}.md"
        out_path.write_text(md_content, encoding="utf-8")
        print(f"Wrote {out_path.name} ({len(records)} comments)")


if __name__ == "__main__":
    main()
