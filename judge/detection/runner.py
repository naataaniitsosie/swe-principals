"""
Detection runner: score each comment in the stratified sample in isolation.

Each comment is scored independently — no surrounding PR thread, no repo
history, no author context. This is what the CONFORMITY system prompt implements.

Reads from:  samples JOIN cleaned  (1,903 rows in the current sample)
Writes to:   scores  (comment_id, model_name) primary key
"""

import logging
from pathlib import Path

from project_config import db_path as default_db_path

from judge.config import ModelInfo, resolve_model
from judge.detection.storage import SamplesReader
from judge.storage import EXPERIMENT_VERSION, ScoresWriter, get_scored_comment_ids

logger = logging.getLogger(__name__)


def _make_judge(info: ModelInfo):
    if info.backend == "openai":
        from judge.gpt_judge import GPTJudge
        return GPTJudge(model=info.tag)
    if info.backend == "openrouter":
        from judge.openrouter_judge import OpenRouterJudge
        return OpenRouterJudge(model=info.tag)
    from judge.ollama_judge import OllamaJudge
    return OllamaJudge(info.tag)


def run(
    model: str,
    limit: int | None = None,
    skip_existing: bool = False,
    repo: str | None = None,
    event_type: str | None = None,
    dry_run: bool = False,
) -> tuple[int, int]:
    """
    Score the stratified sample. Returns (num_scored, num_skipped).
    """
    db = default_db_path()
    info = resolve_model(model)
    logger.info("Model: %s → %s (experiment v%d)", model, info.location, EXPERIMENT_VERSION)

    filters: dict = {}
    if repo and repo.strip():
        filters["repo"] = repo.strip()
    if event_type and event_type.strip():
        filters["event_type"] = event_type.strip()

    if skip_existing:
        scored_ids = get_scored_comment_ids(db, info.tag)
        logger.info("Skipping %d already scored for %s", len(scored_ids), info.tag)
    else:
        scored_ids = set()

    reader = SamplesReader(db, skip_comment_ids=scored_ids, filters=filters)
    records = reader.list_records()
    total = min(len(records), limit) if limit is not None else len(records)

    if dry_run:
        _print_dry_run(records[:total], info)
        return 0, len(scored_ids)

    logger.info(
        "Scoring %d sample comments (model=%s, filters=%s)",
        total, info.tag, filters or "none",
    )

    judge = _make_judge(info)
    writer = ScoresWriter(db)

    num_scored = 0
    batch: list = []
    BATCH_SIZE = 50

    for rec in records:
        if limit is not None and num_scored >= limit:
            break
        comment_id = str(rec["id"])
        try:
            result = judge.score(rec["cleaned_text"])
            base = result.to_row(comment_id, info.tag, rec.get("created_at"))
            # Insert experiment_version at position 2 to match SCORES_SCHEMA column order.
            row = base[:2] + (EXPERIMENT_VERSION,) + base[2:]
            batch.append(row)
            num_scored += 1
            left = total - num_scored
            logger.info(
                "Scored %s (fun=%d nsi=%d insi=%d isi=%d) — %d/%d, %d left",
                comment_id,
                result.fun_score, result.nsi_score, result.insi_score, result.isi_score,
                num_scored, total, left,
            )
        except Exception as e:
            logger.warning("Judge failed for %s: %s", comment_id, e)
            continue

        if len(batch) >= BATCH_SIZE:
            writer.write_batch(batch)
            batch = []

    if batch:
        writer.write_batch(batch)

    logger.info("Done: %d scored, %d skipped.", num_scored, len(scored_ids))
    return num_scored, len(scored_ids)


def _print_dry_run(records: list, info: ModelInfo) -> None:
    from collections import Counter
    strata = Counter(r["stratum_key"] for r in records)
    print(f"\nDry run — {info.tag}  ({info.location})  experiment v{EXPERIMENT_VERSION}")
    print(f"Total comments to score: {len(records)}\n")
    print(f"{'Stratum':<60} {'Count':>5}")
    print("-" * 67)
    for stratum, count in sorted(strata.items()):
        print(f"{stratum:<60} {count:>5}")
    print()
