#!/usr/bin/env python3
"""
CLI for LLM judge: score cleaned PR comments with Ollama (NSI/ISI per CONFORMITY rubric).
Reads from cleaned table, writes to scores table in the same DB. Dedupes by (comment_id, model).
"""
import argparse
import logging
from pathlib import Path

from project_config import db_path, JUDGE_DEFAULT_REPO

from judge.config import DEFAULT_MODEL, SUPPORTED_MODELS
from judge.runner import run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run LLM judge on cleaned PR comments (NSI/ISI scores). Uses Ollama; reads cleaned, writes scores to same DB.",
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default=DEFAULT_MODEL,
        help=f"Model: one of {list(SUPPORTED_MODELS.keys())} or an Ollama tag (e.g. llama3.1:8b). Default: {DEFAULT_MODEL}",
    )
    parser.add_argument(
        "--limit",
        "-n",
        type=int,
        default=None,
        help="Max number of comments to score (for testing). Default: no limit.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip comments that already have a score for this model.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=None,
        help="Path to SQLite DB. Default: project_config.db_path() (e.g. data/raw/events.db).",
    )
    parser.add_argument(
        "--repo",
        "-r",
        type=str,
        default=JUDGE_DEFAULT_REPO,
        help="Only process comments from this repo (owner/name). Default: %(default)s. Use empty string for all repos.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        num_scored, num_skipped = run(
            model=args.model,
            db_path_override=args.db,
            limit=args.limit,
            skip_existing=args.skip_existing,
            repo=args.repo,
        )
        logger.info("Judge finished: %d scored, %d skipped.", num_scored, num_skipped)
        return 0
    except FileNotFoundError as e:
        logger.error("%s", e)
        return 1
    except Exception as e:
        logger.error("Judge failed: %s", e, exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
