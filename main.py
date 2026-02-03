"""
Main entry point for ExpressJS sentiment analysis data extraction.

This script demonstrates how to use the data extraction framework
to pull ExpressJS pull request data from GHArchive.
"""
import logging
from datetime import datetime
from data_extraction import DataExtractor, ExtractionConfig, EXPRESSJS_CONFIG
from data_extraction.config import RepositoryConfig

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """
    Main execution function.
    
    This demonstrates the extraction process:
    1. Configure the extraction (dates, repository, event types)
    2. Initialize the extractor with OOP principles
    3. Execute the extraction
    4. Data is automatically filtered and saved
    """
    
    # Option 1: Use default ExpressJS configuration
    # config = EXPRESSJS_CONFIG
    
    # Option 2: Create custom configuration
    config = ExtractionConfig(
        repository=RepositoryConfig(owner="expressjs", name="express"),
        start_date=datetime(2024, 2, 1),  # Start date
        end_date=datetime(2024, 2, 2),     # End date (2 days for testing)
        event_types=[
            "PullRequestEvent",           # PR open/close/merge events
            "PullRequestReviewEvent",     # PR reviews
            "PullRequestReviewCommentEvent",  # Comments on PR reviews
            "IssueCommentEvent"           # Comments on PRs (PRs are issues)
        ],
        output_dir="./data/raw"
    )
    
    logger.info("=" * 60)
    logger.info("ExpressJS Sentiment Analysis - Data Extraction")
    logger.info("=" * 60)
    logger.info(f"Repository: {config.repository.full_name}")
    logger.info(f"Date Range: {config.start_date.date()} to {config.end_date.date()}")
    logger.info(f"Event Types: {', '.join(config.event_types)}")
    logger.info("=" * 60)
    
    # Initialize extractor (Dependency Injection happens internally)
    extractor = DataExtractor(config)
    
    try:
        # Execute extraction
        output_file = extractor.extract()
        
        logger.info("=" * 60)
        logger.info("Extraction Complete!")
        logger.info(f"Data saved to: {output_file}")
        logger.info("=" * 60)
        
        # Optional: Load and display sample events
        events = extractor.repository.load_events(output_file)
        logger.info(f"\nTotal events extracted: {len(events)}")
        
        if events:
            logger.info("\nSample event:")
            sample = events[0]
            logger.info(f"  Type: {sample.get('type')}")
            logger.info(f"  Actor: {sample.get('actor', {}).get('login')}")
            logger.info(f"  Created: {sample.get('created_at')}")
        
    except Exception as e:
        logger.error(f"Extraction failed: {e}", exc_info=True)
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
