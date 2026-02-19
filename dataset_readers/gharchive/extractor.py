"""
GHArchive extraction orchestrator.
Fetches, filters, and persists GitHub events from data.gharchive.org.
Fetches each hour once, partitions by repo, and appends to disk immediately (streaming;
does not load all events into memory).
"""
import logging
from collections import defaultdict
from typing import List, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from dataset_readers.gharchive.storage import StreamingWriter

from dataset_readers.gharchive.config import ExtractionConfig
from dataset_readers.gharchive.client import GHArchiveClient, RequestsHTTPClient
from dataset_readers.gharchive.filters import EventFilterPipeline, HasTextContentFilter
from dataset_readers.gharchive.storage import DataRepository, JSONLinesStorage

logger = logging.getLogger(__name__)


class DataExtractor:
    """Orchestrates GHArchive extraction: fetch once per hour, filter, stream to one file per repo."""

    def __init__(self, config: ExtractionConfig):
        self.config = config
        http_client = RequestsHTTPClient(timeout=60)
        self.client = GHArchiveClient(http_client)
        # Client pre-filters by repo + event type; we only drop events without text.
        self.filter_pipeline = EventFilterPipeline(HasTextContentFilter())
        storage = JSONLinesStorage(config.output_dir)
        self.repository = DataRepository(storage)

    def extract(self) -> List[Tuple[str, str]]:
        """
        Fetch each hour once, filter to configured repos and event types, partition by repo,
        and append each hour's events to the repo's file. Memory is bounded by one hour of
        filtered events per repo, not the full date range. Returns list of (repo_full_name, file_path).
        """
        repo_names = [r.full_name for r in self.config.repositories]

        # One streaming writer per repo; events are appended each hour, not held in memory
        writers: dict[str, Tuple[str, "StreamingWriter"]] = {}  # repo_key -> (full_name, writer)
        for repo_config in self.config.repositories:
            full_name = repo_config.full_name
            writer = self.repository.create_extraction_writer(
                repository=full_name,
                start_date=self.config.start_date,
                end_date=self.config.end_date,
            )
            writers[full_name.lower()] = (full_name, writer)

        logger.info(
            "Starting extraction for %d repo(s): %s",
            len(repo_names),
            ", ".join(repo_names),
        )
        logger.info("Date range: %s to %s", self.config.start_date, self.config.end_date)

        try:
            # Client pre-filters by repo + event type while streaming so we only
            # hold matching events in memory; then we run HasTextContentFilter here.
            for hourly_events in self.client.fetch_date_range(
                self.config.start_date,
                self.config.end_date,
                repo_names=set(repo_names),
                event_types=set(self.config.event_types),
            ):
                filtered_events = self.filter_pipeline.filter_events(hourly_events)
                by_repo: dict[str, list] = defaultdict(list)
                for event in filtered_events:
                    by_repo[event.get("repo", {}).get("name", "").lower()].append(event)
                for repo_key, events in by_repo.items():
                    full_name, writer = writers[repo_key]
                    writer.append_events(events)
                stats = self.filter_pipeline.get_stats()
                logger.info(
                    "Found %s events from matching repos, matched %s with text",
                    stats["total"],
                    stats["matched"],
                )

            output_files: List[Tuple[str, str]] = []
            for full_name, writer in writers.values():
                file_path = writer.finalize(
                    additional_metadata={
                        "filter_stats": self.filter_pipeline.get_stats(),
                        "repo_count": len(self.config.repositories),
                    },
                )
                output_files.append((full_name, file_path))
                logger.info("Wrote %s events for %s -> %s", writer.count, full_name, file_path)

            return output_files
        except Exception as e:
            logger.error("Extraction failed: %s", e)
            raise
