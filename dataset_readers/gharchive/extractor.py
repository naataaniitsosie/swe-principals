"""
GHArchive extraction orchestrator.
Fetches, filters, and persists GitHub events from data.gharchive.org.
"""
import logging
from typing import List

from dataset_readers.gharchive.config import ExtractionConfig
from dataset_readers.gharchive.client import GHArchiveClient, RequestsHTTPClient
from dataset_readers.gharchive.filters import (
    EventFilterPipeline,
    CompositeFilter,
    RepositoryFilter,
    EventTypeFilter,
    HasTextContentFilter,
)
from dataset_readers.gharchive.storage import DataRepository, JSONLinesStorage
from dataset_readers.gharchive.models import GitHubEvent

logger = logging.getLogger(__name__)


class DataExtractor:
    """Orchestrates GHArchive extraction: fetch, filter, persist."""

    def __init__(self, config: ExtractionConfig):
        self.config = config
        http_client = RequestsHTTPClient(timeout=60)
        self.client = GHArchiveClient(http_client)
        filters = CompositeFilter(
            [
                RepositoryFilter(config.repository.full_name),
                EventTypeFilter(config.event_types),
                HasTextContentFilter(),
            ]
        )
        self.filter_pipeline = EventFilterPipeline(filters)
        storage = JSONLinesStorage(config.output_dir)
        self.repository = DataRepository(storage)

    def extract(self) -> str:
        logger.info(f"Starting extraction for {self.config.repository.full_name}")
        logger.info(f"Date range: {self.config.start_date} to {self.config.end_date}")

        all_events = []
        try:
            for hourly_events in self.client.fetch_date_range(
                self.config.start_date,
                self.config.end_date,
            ):
                filtered_events = self.filter_pipeline.filter_events(hourly_events)
                all_events.extend(filtered_events)
                stats = self.filter_pipeline.get_stats()
                logger.info(
                    f"Processed {stats['total']} events, "
                    f"matched {stats['matched']}, "
                    f"total accumulated: {len(all_events)}"
                )

            file_path = self.repository.save_extracted_events(
                events=all_events,
                repository=self.config.repository.full_name,
                start_date=self.config.start_date,
                end_date=self.config.end_date,
                additional_metadata={
                    "filter_stats": self.filter_pipeline.get_stats()
                },
            )
            logger.info(f"Extraction complete! Saved {len(all_events)} events to {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            raise

    def extract_and_convert_to_models(self) -> List[GitHubEvent]:
        file_path = self.extract()
        raw_events = self.repository.load_events(file_path)
        events = []
        for raw_event in raw_events:
            try:
                events.append(GitHubEvent.from_dict(raw_event))
            except (ValueError, KeyError) as e:
                logger.warning(f"Failed to parse event: {e}")
        return events
