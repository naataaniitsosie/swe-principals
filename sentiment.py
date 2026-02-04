"""
Sentiment analysis entry point.
Run POC sentiment models on existing extracted JSONL (from dataset.py).
"""
import argparse
import logging

from sentiment_analysis.runner import run_analysis

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args():
    parser = argparse.ArgumentParser(
        description="Run sentiment analysis on extracted PR event data (JSONL).",
    )
    parser.add_argument(
        "input",
        type=str,
        default="./data/raw",
        nargs="?",
        help="Path to a .jsonl file or directory of .jsonl files (default: ./data/raw)",
    )
    parser.add_argument(
        "--output-dir",
        "-o",
        type=str,
        default="./data/sentiment",
        help="Output directory for sentiment results (default: ./data/sentiment)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        out_path = run_analysis(
            input_path=args.input,
            output_dir=args.output_dir,
        )
        logger.info("Sentiment results written to %s", out_path)
        return 0
    except FileNotFoundError as e:
        logger.error("%s", e)
        return 1
    except Exception as e:
        logger.error("Sentiment analysis failed: %s", e, exc_info=True)
        return 1


if __name__ == "__main__":
    exit(main())
