"""
Preprocess PR events: read from events table, run filtering and text cleaning, write cleaned table.
Steps: dedupe by id, drop bot/CI and trivial comments, extract text, strip code/images/diff, lowercase and tokenize, drop if < 2 tokens; output slim records (id, cleaned_text, repo, created_at, type, author_association, tokens). DB path from project_config (DATA_DIR / DB_FILENAME). No CLI options.
"""
import logging
from pathlib import Path

from project_config import DATA_DIR
from preprocessing.pipeline import CleanerPipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> int:
    data_dir = Path(DATA_DIR)
    if not data_dir.is_dir():
        logger.error("Data directory does not exist: %s (set DATA_DIR in project_config.py)", data_dir)
        return 1

    pipeline = CleanerPipeline(str(data_dir))
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
