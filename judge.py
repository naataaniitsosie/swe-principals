#!/usr/bin/env python3
"""
CLI for LLM detection judge: score stratified sample PR comments (FUN/NSI/INSI/ISI).
Reads from the `samples` table; writes to `scores` in the project DB.
"""

import argparse
import logging

from judge.config import MODEL_REGISTRY
from judge.detection.runner import run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


# Build the model table for --help
_MODEL_LINES = "\n".join(
    f"  {name:<16}  {info.location}"
    for name, info in MODEL_REGISTRY.items()
)
_MODEL_HELP = f"Model to use. Determines the backend automatically.\n\nAvailable:\n{_MODEL_LINES}"


def parse_args():
    parser = argparse.ArgumentParser(
        description=(
            "Score stratified sample PR comments with an LLM judge (FUN/NSI/INSI/ISI).\n"
            "Source: `samples` table (stratified, 1 903 rows).\n"
            "Output: `scores` table — (comment_id, model_name) primary key."
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--model", "-m",
        type=str,
        required=True,
        metavar="NAME",
        help=_MODEL_HELP + "\n\nSmoke test models (gemma4-e4b, starcoder2-3b) are fast but low-quality; use only to verify the pipeline before a full run.",
    )
    parser.add_argument(
        "--limit", "-n",
        type=int,
        default=None,
        help="Max comments to score. Useful for smoke tests.",
    )
    parser.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip (comment_id, model) pairs that already have a successful score.",
    )
    parser.add_argument(
        "--repo", "-r",
        type=str,
        default=None,
        metavar="OWNER/NAME",
        help="Restrict to one repo (e.g. expressjs/express).",
    )
    parser.add_argument(
        "--event-type", "-e",
        type=str,
        default=None,
        metavar="TYPE",
        help="Restrict to one event type (e.g. PullRequestReviewCommentEvent).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print per-stratum comment counts without calling the model.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        num_scored, num_skipped = run(
            model=args.model,
            limit=args.limit,
            skip_existing=args.skip_existing,
            repo=args.repo,
            event_type=args.event_type,
            dry_run=args.dry_run,
        )
        if not args.dry_run:
            logger.info("Finished: %d scored, %d skipped.", num_scored, num_skipped)
        return 0
    except FileNotFoundError as e:
        logger.error("%s", e)
        return 1
    except Exception as e:
        logger.error("Judge failed: %s", e, exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
