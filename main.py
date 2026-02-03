"""
Main entry point for ExpressJS sentiment analysis data extraction.

Supports multiple dataset readers via --dataset-reader flag.
Default: gharchive
"""
import argparse
import logging
from datetime import datetime

from dataset_readers.config import RepositoryConfig
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
        description="Extract ExpressJS pull request data for sentiment analysis.",
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
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./data/raw",
        help="Output directory for extracted data",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    repository = RepositoryConfig(owner="expressjs", name="express")
    start_date = datetime.strptime(args.start_date, "%Y-%m-%d")
    end_date = datetime.strptime(args.end_date, "%Y-%m-%d")
    event_types = [
        "PullRequestEvent",
        "PullRequestReviewEvent",
        "PullRequestReviewCommentEvent",
        "IssueCommentEvent",
    ]

    logger.info("=" * 60)
    logger.info("ExpressJS Sentiment Analysis - Data Extraction")
    logger.info("=" * 60)
    logger.info(f"Dataset reader: {args.dataset_reader}")
    logger.info(f"Repository: {repository.full_name}")
    logger.info(f"Date range: {start_date.date()} to {end_date.date()}")
    logger.info(f"Event types: {', '.join(event_types)}")
    logger.info("=" * 60)

    try:
        reader = get_reader(
            args.dataset_reader,
            repository=repository,
            start_date=start_date,
            end_date=end_date,
            event_types=event_types,
            output_dir=args.output_dir,
        )
    except KeyError as e:
        logger.error(str(e))
        return 1

    try:
        output_file = reader.extract()

        logger.info("=" * 60)
        logger.info("Extraction Complete!")
        logger.info(f"Data saved to: {output_file}")
        logger.info("=" * 60)

        if hasattr(reader, "load_events"):
            try:
                events = reader.load_events(output_file)
                logger.info(f"\nTotal events extracted: {len(events)}")
                if events:
                    sample = events[0]
                    logger.info("\nSample event:")
                    logger.info(f"  Type: {sample.get('type')}")
                    logger.info(f"  Actor: {sample.get('actor', {}).get('login')}")
                    logger.info(f"  Created: {sample.get('created_at')}")
            except NotImplementedError:
                pass

    except Exception as e:
        logger.error(f"Extraction failed: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
