#!/usr/bin/env python3
"""
Convert preprocessed JSONL (one per repo) to a single Markdown file per repo,
organized by date. Use for scrolling through comments with full metadata.
"""
import argparse
import json
from pathlib import Path
from collections import defaultdict
from typing import List


def load_jsonl(path: Path) -> List[dict]:
    records = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


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


def jsonl_to_md(records: List[dict], repo_label: str) -> str:
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
        description="Convert preprocessed JSONL in a directory to Markdown per repo, organized by date."
    )
    parser.add_argument(
        "input_dir",
        type=Path,
        help="Directory containing .jsonl files; one .md per .jsonl, written to the same directory.",
    )
    args = parser.parse_args()

    input_dir = args.input_dir
    if not input_dir.is_dir():
        raise SystemExit(f"Not a directory: {input_dir}")

    for path in sorted(input_dir.glob("*.jsonl")):
        records = load_jsonl(path)
        if not records:
            print(f"Skip (empty): {path.name}")
            continue

        repo_label = records[0].get("repo") or path.stem
        md_content = jsonl_to_md(records, repo_label)
        out_path = path.with_suffix(".md")
        out_path.write_text(md_content, encoding="utf-8")
        print(f"Wrote {out_path.name} ({len(records)} comments)")


if __name__ == "__main__":
    main()
