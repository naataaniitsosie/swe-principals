#!/usr/bin/env python3
"""
CLI for LLM judge: score cleaned PR comments (FUN/NSI/INSI/ISI per CONFORMITY_SYSTEM_PROMPT).
Reads from cleaned table, writes to scores table in the same DB. Dedupes by (comment_id, model).
"""
import argparse
import logging
from pathlib import Path

from project_config import JUDGE_DEFAULT_REPO

from judge.config import DEFAULT_MODEL, DEFAULT_OPENAI_MODEL, SUPPORTED_MODELS, Backend
from judge.runner import run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

_MODEL_HELP = (
    f"Model identifier. "
    f"Ollama backend: short name {list(SUPPORTED_MODELS.keys())} or a full Ollama tag; "
    f"default if omitted: {DEFAULT_MODEL!r}. "
    f"OpenAI backend: API model id (e.g. {DEFAULT_OPENAI_MODEL!r}); "
    f"default if omitted: {DEFAULT_OPENAI_MODEL!r}."
)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run LLM judge on cleaned PR comments (FUN/NSI/INSI/ISI scores). "
        "Backends: Ollama (local) or OpenAI API. Reads cleaned, writes scores to same DB.",
    )
    parser.add_argument(
        "--backend",
        "-b",
        type=str,
        choices=("ollama", "openai"),
        default="ollama",
        help="ollama (default): local Ollama. openai: OpenAI Chat Completions (requires OPENAI_API_TOKEN).",
    )
    parser.add_argument(
        "--model",
        "-m",
        type=str,
        default=None,
        metavar="NAME",
        help=_MODEL_HELP,
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
    backend: Backend = args.backend  # type: ignore[assignment]
    try:
        num_scored, num_skipped = run(
            model=args.model,
            backend=backend,
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
