#!/usr/bin/env python3
"""
Print cleaned PR comments with LLM judge scores in a human-readable layout similar to
docs/papers/CONFORMITY_SYSTEM_PROMPT.md (Input + FUN/NSI/INSI/ISI scores and reasoning).

Joins scores + cleaned + events for repo/created_at metadata. Default: random sample; use
--all for every row for the model, or --comment-id for one id.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

import project_config  # noqa: F401 — load `.env` if present

from project_config import db_path


def _repo_and_created_at(event: dict) -> tuple[str, str]:
    """Minimal metadata from raw event_data (matches preprocessing.workflow metadata fields we display)."""
    repo = event.get("repo") or {}
    repo_name = repo.get("name", "") if isinstance(repo, dict) else ""
    created_at = event.get("created_at") or ""
    return repo_name, created_at


def _fetch_rows(
    conn: sqlite3.Connection,
    model_name: str,
    comment_id: str | None,
    sample_n: int | None,
    *,
    sample_random: bool,
) -> list[dict]:
    """
    Return list of dicts with keys: id, cleaned_text, model_name, repo, created_at,
    fun_score, fun_reasoning, nsi_score, nsi_reasoning, insi_score, insi_reasoning,
    isi_score, isi_reasoning, score_created_at.
    """
    base = """
        SELECT
            s.comment_id,
            c.cleaned_text,
            s.model_name,
            s.fun_score,
            s.fun_reasoning,
            s.nsi_score,
            s.nsi_reasoning,
            s.insi_score,
            s.insi_reasoning,
            s.isi_score,
            s.isi_reasoning,
            s.created_at AS score_created_at,
            e.event_data
        FROM scores s
        INNER JOIN cleaned c ON c.id = s.comment_id
        INNER JOIN events e ON e.id = s.comment_id
        WHERE s.model_name = ?
    """
    params: list = [model_name]
    if comment_id is not None:
        base += " AND s.comment_id = ?"
        params.append(comment_id)

    if comment_id is not None:
        sql = base + " LIMIT 1"
        cur = conn.execute(sql, params)
    elif sample_random and sample_n is not None and sample_n > 0:
        sql = base + " ORDER BY RANDOM() LIMIT ?"
        params.append(sample_n)
        cur = conn.execute(sql, params)
    else:
        # --all: stable order
        sql = base + " ORDER BY s.comment_id"
        cur = conn.execute(sql, params)

    rows: list[dict] = []
    for row in cur:
        (
            cid,
            cleaned_text,
            mname,
            fun_score,
            fun_reasoning,
            nsi_score,
            nsi_reasoning,
            insi_score,
            insi_reasoning,
            isi_score,
            isi_reasoning,
            score_created_at,
            event_data_str,
        ) = row
        try:
            event_data = json.loads(event_data_str)
            repo, created_at = _repo_and_created_at(event_data)
        except (json.JSONDecodeError, TypeError):
            repo = ""
            created_at = ""
        rows.append(
            {
                "id": cid,
                "cleaned_text": cleaned_text or "",
                "model_name": mname,
                "repo": repo,
                "created_at": created_at,
                "fun_score": int(fun_score),
                "fun_reasoning": fun_reasoning or "",
                "nsi_score": int(nsi_score),
                "nsi_reasoning": nsi_reasoning or "",
                "insi_score": int(insi_score),
                "insi_reasoning": insi_reasoning or "",
                "isi_score": int(isi_score),
                "isi_reasoning": isi_reasoning or "",
                "score_created_at": score_created_at,
            }
        )
    return rows


def _tags_from_scores(r: dict) -> str:
    """Comma-separated dimension tags for non-zero scores (paper-style Tags line)."""
    tags = []
    if r["fun_score"] > 0:
        tags.append("FUN")
    if r["nsi_score"] > 0:
        tags.append("NSI")
    if r["insi_score"] > 0:
        tags.append("INSI")
    if r["isi_score"] > 0:
        tags.append("ISI")
    return ", ".join(tags) if tags else "(none)"


def format_record(index: int, r: dict) -> str:
    """Format one comment + scores like CONFORMITY_SYSTEM_PROMPT / codebook style."""
    text = r["cleaned_text"] or "(empty)"
    lines = [
        f"### {index}.",
        "",
        f"- **id:** `{r['id']}`",
        f"- **repo:** {r['repo']}",
        f"- **created_at:** {r['created_at']}",
        f"- **model:** `{r['model_name']}`",
        "",
        "*Input:*",
        "```",
        text,
        "```",
        "",
        f"Tags: {_tags_from_scores(r)}",
        "",
        f"FUN Score: {r['fun_score']}",
        f"FUN Reasoning: {r['fun_reasoning']}",
        "",
        f"NSI Score: {r['nsi_score']}",
        f"NSI Reasoning: {r['nsi_reasoning']}",
        "",
        f"INSI Score: {r['insi_score']}",
        f"INSI Reasoning: {r['insi_reasoning']}",
        "",
        f"ISI Score: {r['isi_score']}",
        f"ISI Reasoning: {r['isi_reasoning']}",
        "",
        "---",
        "",
    ]
    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Print comments with judge scores (FUN/NSI/INSI/ISI) in a CONFORMITY-style layout. "
            "--model must match scores.model_name exactly (see: "
            "SELECT DISTINCT model_name FROM scores)."
        ),
    )
    p.add_argument(
        "--model",
        "-m",
        required=True,
        help="Judge model id as stored in scores (same string you passed to judge.py).",
    )
    p.add_argument(
        "--db",
        type=Path,
        default=None,
        help="SQLite DB path. Default: project_config.db_path().",
    )
    p.add_argument(
        "--comment-id",
        "-c",
        type=str,
        default=None,
        metavar="ID",
        help="Show only this comment id (ignores --sample-n / --all).",
    )
    g = p.add_mutually_exclusive_group()
    g.add_argument(
        "--sample-n",
        "-n",
        type=int,
        default=20,
        dest="sample_n",
        metavar="N",
        help="Random sample size (default: 20). Ignored with --all or --comment-id.",
    )
    g.add_argument(
        "--all",
        action="store_true",
        help="Print every scored row for this model (ordered by comment_id).",
    )
    return p.parse_args()


def main() -> int:
    args = parse_args()
    path = args.db or db_path()
    if not path.exists():
        print(f"Database not found: {path}", file=sys.stderr)
        return 1

    model_name = str(args.model).strip()
    if not model_name:
        print("--model is required", file=sys.stderr)
        return 1

    conn = sqlite3.connect(str(path))
    try:
        if args.comment_id:
            sample_n = None
            sample_random = False
        elif args.all:
            sample_n = None
            sample_random = False
        else:
            sample_n = max(1, int(args.sample_n))
            sample_random = True

        rows = _fetch_rows(
            conn,
            model_name,
            args.comment_id,
            sample_n,
            sample_random=sample_random,
        )
    finally:
        conn.close()

    if not rows:
        print(
            f"No rows found for model={model_name!r}"
            + (f" comment_id={args.comment_id!r}" if args.comment_id else "")
            + ". Check model name: sqlite3 ... \"SELECT DISTINCT model_name FROM scores;\"",
            file=sys.stderr,
        )
        return 2

    parts = [
        "# Browse scores",
        "",
        f"**Model:** `{model_name}`",
        f"**Rows:** {len(rows)}",
        "",
        "---",
        "",
    ]
    for i, r in enumerate(rows, start=1):
        parts.append(format_record(i, r))

    sys.stdout.write("\n".join(parts).rstrip() + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
