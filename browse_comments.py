#!/usr/bin/env python3
"""
Convert preprocessed events from the single SQLite DB to Markdown files per repo,
organized by date. Uses project_config for DB and output directory. No CLI options.
"""
import json
import sqlite3
from pathlib import Path
from collections import defaultdict
from typing import List

from project_config import DATA_DIR, db_path


def _table_for_db(conn: sqlite3.Connection) -> str:
    """Table to read from; always events."""
    return "events"


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


def _body_from_record(rec: dict) -> str:
    """Get body text: from cleaned record, or extract from raw event payload."""
    if rec.get("body"):
        return rec.get("body") or ""
    payload = rec.get("payload") or {}
    ev_type = rec.get("type") or ""
    if ev_type == "PullRequestEvent":
        pr = payload.get("pull_request") or {}
        title = pr.get("title", "")
        body = pr.get("body", "")
        return f"{title}\n{body}".strip() if body else (title or "")
    if ev_type in ("IssueCommentEvent", "PullRequestReviewCommentEvent"):
        return (payload.get("comment") or {}).get("body", "")
    if ev_type == "PullRequestReviewEvent":
        return (payload.get("review") or {}).get("body", "")
    return ""


def record_to_md(rec: dict, number: int) -> str:
    """Format one record as Markdown: number, metadata block, body, and cleaned text."""
    body_text = _body_from_record(rec)
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
        "**body:**",
        body_text or "(empty)",
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
    data_dir = Path(DATA_DIR)
    path_to_db = db_path()
    if not data_dir.is_dir():
        raise SystemExit(f"Data directory does not exist: {data_dir} (set DATA_DIR in project_config.py)")
    if not path_to_db.exists():
        raise SystemExit(f"Database not found: {path_to_db}")

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
