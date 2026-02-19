"""
Preprocess PR event data produced by dataset.py (CONFORMITY.md Preprocessing).
Reads only from the SQLite DB (events table); no JSONL. Removes bot/CI and trivial comments;
strips code blocks and diff snippets; lowercases and tokenizes. Writes cleaned table to same DB.
Input/output: single DB in project config data dir (default data/raw).
"""
import argparse
import logging
from pathlib import Path

from project_config import DATA_DIR
from preprocessing.pipeline import CleanerPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Preprocess extracted PR event data (remove bots/trivial, strip code/diff, tokenize).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Input/output: single DB in project config dir; adds cleaned table.",
    )
    parser.add_argument(
        "--input-dir",
        "-i",
        type=str,
        default=None,
        help="Directory containing events.db (default: from project_config, data/raw)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    data_dir = Path(args.input_dir) if args.input_dir else DATA_DIR
    if not data_dir.is_dir():
        logger.error("Input directory does not exist: %s", data_dir)
        return 1

    pipeline = CleanerPipeline(str(data_dir), str(data_dir))
    results = pipeline.run()

    if not results:
        logger.warning("No events.db found in %s", data_dir)
        return 0

    total_read = sum(r[1] for r in results)
    total_duplicates = sum(r[2] for r in results)
    total_written = sum(r[3] for r in results)
    logger.info("Total: read %s, duplicates %s, kept %s", total_read, total_duplicates, total_written)
    return 0


if __name__ == "__main__":
    exit(main())
