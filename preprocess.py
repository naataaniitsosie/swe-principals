"""
Preprocess PR event data produced by dataset.py (CONFORMITY.md Preprocessing).
Removes bot/CI and trivial comments; strips code blocks and diff snippets; lowercases and tokenizes.
Input: JSONL from dataset.py (e.g. ./data/raw). Output: JSONL with cleaned_text and tokens (e.g. ./data/cleaned).
"""
import argparse
import logging
from pathlib import Path

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
        epilog="Input: directory of .jsonl from dataset.py. Output: same filenames with cleaned_text and tokens.",
    )
    parser.add_argument(
        "--input-dir",
        "-i",
        type=str,
        default="./data/raw",
        help="Directory containing raw .jsonl files from dataset.py (default: ./data/raw)",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default="./data/cleaned",
        help="Directory to write preprocessed .jsonl files (default: ./data/cleaned)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    input_dir = Path(args.input_dir)
    if not input_dir.is_dir():
        logger.error("Input directory does not exist: %s", input_dir)
        return 1

    pipeline = CleanerPipeline(str(input_dir), args.output_dir)
    results = pipeline.run()

    if not results:
        logger.warning("No .jsonl files found in %s", input_dir)
        return 0

    total_read = sum(r[1] for r in results)
    total_written = sum(r[2] for r in results)
    logger.info("Total: read %s events, kept %s", total_read, total_written)
    return 0


if __name__ == "__main__":
    exit(main())
