"""
Data extraction entry point.
Extract PR event data via dataset readers (default: GHArchive).
Repositories match CONFORMITY.md "Repositories Under Investigation".
"""
import argparse
import logging
from datetime import datetime

from dataset_readers.gharchive.config import REPOSITORIES, DEFAULT_EVENT_TYPES
from dataset_readers import (
    get_reader,
    get_default_reader_name,
    list_readers,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract pull request data for conformity/sentiment analysis.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"Available readers: {', '.join(list_readers())}",
    )
    parser.add_argument(
        "--dataset-reader",
        "-r",
        type=str,
        default=get_default_reader_name(),
        help=f"Dataset reader to use (default: {get_default_reader_name()})",
    )
    parser.add_argument(
        "--start-date",
        type=str,
        default="2024-02-01",
        help="Start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default="2024-02-02",
        help="End date (YYYY-MM-DD)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    repositories = REPOSITORIES
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    event_types = DEFAULT_EVENT_TYPES

    logger.info("=" * 60)
    logger.info("GitHub Pull Request - Data Extraction")
    logger.info("=" * 60)
    logger.info(f"Dataset reader: {args.dataset_reader}")
    logger.info("Repositories: %d — %s", len(repositories), ", ".join(r.full_name for r in repositories))
    logger.info("Date range: %s to %s", start_date.date(), end_date.date())
    logger.info("Event types: %s", ", ".join(event_types))
    logger.info("=" * 60)

    try:
        reader = get_reader(
            args.dataset_reader,
            repositories=repositories,
            start_date=start_date,
            end_date=end_date,
            event_types=event_types,
        )
    except KeyError as e:
        logger.error(str(e))
        return 1
    except TypeError as e:
        logger.error("Reader does not support repositories= (e.g. bigquery): %s", e)
        return 1

    try:
        output_files = reader.extract()
        # One DB for all repos; path is repeated per repo for API compatibility
        out_path = output_files[0][1] if output_files else None
        repo_names = [name for name, _ in output_files]
        if out_path:
            logger.info("Extracted to %s (%d repos: %s)", out_path, len(repo_names), ", ".join(repo_names))
    except Exception as e:
        logger.error("Extraction failed: %s", e, exc_info=True)
        return 1

    logger.info("=" * 60)
    logger.info("Extraction complete. Output: %s", out_path)
    logger.info("=" * 60)
    return 0


if __name__ == "__main__":
    exit(main())
