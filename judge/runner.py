"""
Orchestration: read cleaned rows, run Ollama judge per comment, write scores with dedupe.
"""
import logging
from pathlib import Path

from project_config import db_path

from judge.config import resolve_model, DEFAULT_MODEL
from judge.storage import CleanedReader, ScoresWriter, get_scored_comment_ids
from judge.ollama_judge import OllamaJudge

logger = logging.getLogger(__name__)


def run(
    model: str,
    db_path_override: Path | None = None,
    limit: int | None = None,
    skip_existing: bool = False,
    repo: str | None = None,
) -> tuple[int, int]:
    """
    Run the judge on cleaned comments. Returns (num_scored, num_skipped).
    If repo is set, only process comments from that repo (owner/name, e.g. expressjs/express).
    """
    path = db_path_override or db_path()
    model_tag = resolve_model(model)

    if skip_existing:
        scored_ids = get_scored_comment_ids(path, model_tag)
        logger.info("Skipping %d comments already scored for model %s", len(scored_ids), model_tag)
    else:
        scored_ids = set()

    filters = {}
    if repo and str(repo).strip():
        filters["repo"] = str(repo).strip()
    reader = CleanedReader(
        path,
        skip_comment_ids=scored_ids if skip_existing else None,
        filters=filters,
    )
    records = reader.list_records()
    total_to_score = min(len(records), limit) if limit is not None else len(records)
    if filters:
        logger.info("Will score %d comments (filters=%s, model=%s)", total_to_score, filters, model_tag)
    else:
        logger.info("Will score %d comments (model=%s)", total_to_score, model_tag)

    writer = ScoresWriter(path)
    judge = OllamaJudge(model_tag)

    num_scored = 0
    num_skipped = len(scored_ids) if skip_existing else 0
    batch = []
    batch_size = 50

    for rec in records:
        if limit is not None and num_scored >= limit:
            break
        comment_id = str(rec.get("id", ""))
        cleaned_text = rec.get("cleaned_text") or ""
        created_at = rec.get("created_at")

        try:
            result = judge.score(cleaned_text)
            row = result.to_row(comment_id, model_tag, created_at)
            batch.append(row)
            num_scored += 1
            left = total_to_score - num_scored
            logger.info(
                "Scored comment %s (nsi=%d, isi=%d) — %d/%d done, %d left",
                comment_id,
                result.nsi_score,
                result.isi_score,
                num_scored,
                total_to_score,
                left,
            )
        except Exception as e:
            logger.warning("Judge failed for comment %s: %s", comment_id, e)
            continue

        if len(batch) >= batch_size:
            writer.write_batch(batch)
            batch = []

    if batch:
        writer.write_batch(batch)

    logger.info("Done. Scored %d comments, skipped %d (existing).", num_scored, num_skipped)
    return num_scored, num_skipped
