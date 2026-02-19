"""
GHArchive extraction orchestrator.
Fetches and persists GitHub events from data.gharchive.org.
Fetches each hour once; client filters by repo and event type. Matching events go to one SQLite DB.
"""
import logging
from pathlib import Path
from typing import List, Tuple

from dataset_readers.gharchive.config import ExtractionConfig
from dataset_readers.gharchive.client import GHArchiveClient, RequestsHTTPClient
from dataset_readers.gharchive.storage import DataRepository, SQLiteStorage, get_raw_db_stats

logger = logging.getLogger(__name__)


class DataExtractor:
    """Orchestrates GHArchive extraction: fetch once per hour (repo + event type filter in client), stream to one DB."""

    def __init__(self, config: ExtractionConfig):
        self.config = config
        http_client = RequestsHTTPClient(timeout=60)
        self.client = GHArchiveClient(http_client)
        storage = SQLiteStorage(config.output_dir)
        self.repository = DataRepository(storage)

    def extract(self) -> List[Tuple[str, str]]:
        """
        Fetch each hour once; client returns events for configured repos and event types. Append to one DB.
        Returns list of (repo_full_name, db_path); db_path is the same for all.
        """
        repo_names = [r.full_name for r in self.config.repositories]
        writer = self.repository.create_extraction_writer()

        logger.info(
            "Starting extraction for %d repo(s): %s",
            len(repo_names),
            ", ".join(repo_names),
        )
        logger.info("Date range: %s to %s", self.config.start_date, self.config.end_date)
        logger.info("Event types: %s", ", ".join(self.config.event_types))

        try:
            for hourly_events in self.client.fetch_date_range(
                self.config.start_date,
                self.config.end_date,
                repo_names=set(repo_names),
                event_types=set(self.config.event_types),
            ):
                writer.append_events(hourly_events)
                logger.info("Events this hour: %d", len(hourly_events))

            db_path_str = writer.finalize(
                additional_metadata={
                    "repo_count": len(self.config.repositories),
                    "repos": repo_names,
                },
            )
            logger.info("Wrote %s events this run -> %s", writer.count, db_path_str)
            # Final DB stats (raw data)
            stats = get_raw_db_stats(Path(db_path_str))
            size_mb = stats["size_bytes"] / (1024 * 1024)
            logger.info(
                "DB stats: %s | %.2f MiB | %d total rows",
                stats["path"],
                size_mb,
                stats["total_rows"],
            )
            for repo, count in sorted(stats["by_repo"].items()):
                logger.info("  %s: %d", repo, count)
            return [(name, db_path_str) for name in repo_names]
        except Exception as e:
            logger.error("Extraction failed: %s", e)
            raise
