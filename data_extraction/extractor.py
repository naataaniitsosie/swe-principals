"""
Main orchestrator for data extraction process.
Follows Facade Pattern to provide simple interface to complex subsystem.
"""
import logging
from typing import List
from data_extraction.config import ExtractionConfig
from data_extraction.gharchive_client import GHArchiveClient, RequestsHTTPClient
from data_extraction.filters import (
    EventFilterPipeline,
    CompositeFilter,
    RepositoryFilter,
    EventTypeFilter,
    HasTextContentFilter
)
from data_extraction.storage import DataRepository, JSONLinesStorage
from data_extraction.models import GitHubEvent

logger = logging.getLogger(__name__)


class DataExtractor:
    """
    Main orchestrator for extracting ExpressJS data from GHArchive.
    
    This class coordinates the entire extraction process:
    1. Fetching data from GHArchive
    2. Filtering relevant events
    3. Persisting to storage
    
    Follows Single Responsibility Principle by delegating specific tasks
    to specialized components.
    """
    
    def __init__(self, config: ExtractionConfig):
        """
        Initialize extractor with configuration.
        
        Args:
            config: Extraction configuration
        """
        self.config = config
        
        # Initialize dependencies (Dependency Injection)
        http_client = RequestsHTTPClient(timeout=60)
        self.client = GHArchiveClient(http_client)
        
        # Setup filtering pipeline
        filters = CompositeFilter([
            RepositoryFilter(config.repository.full_name),
            EventTypeFilter(config.event_types),
            HasTextContentFilter()
        ])
        self.filter_pipeline = EventFilterPipeline(filters)
        
        # Setup storage
        storage = JSONLinesStorage(config.output_dir)
        self.repository = DataRepository(storage)
    
    def extract(self) -> str:
        """
        Execute the extraction process.
        
        Returns:
            Path to saved data file
            
        This method orchestrates the entire workflow:
        1. Fetch hourly data from GHArchive
        2. Filter for ExpressJS events
        3. Accumulate matching events
        4. Save to persistent storage
        """
        logger.info(f"Starting extraction for {self.config.repository.full_name}")
        logger.info(f"Date range: {self.config.start_date} to {self.config.end_date}")
        
        all_events = []
        
        try:
            # Fetch data in hourly batches (generator pattern for memory efficiency)
            for hourly_events in self.client.fetch_date_range(
                self.config.start_date,
                self.config.end_date
            ):
                # Filter events
                filtered_events = self.filter_pipeline.filter_events(hourly_events)
                all_events.extend(filtered_events)
                
                # Log progress
                stats = self.filter_pipeline.get_stats()
                logger.info(
                    f"Processed {stats['total']} events, "
                    f"matched {stats['matched']}, "
                    f"total accumulated: {len(all_events)}"
                )
            
            # Save results
            file_path = self.repository.save_extracted_events(
                events=all_events,
                repository=self.config.repository.full_name,
                start_date=self.config.start_date,
                end_date=self.config.end_date,
                additional_metadata={'filter_stats': self.filter_pipeline.get_stats()}
            )
            
            logger.info(f"Extraction complete! Saved {len(all_events)} events to {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Extraction failed: {e}")
            raise
    
    def extract_and_convert_to_models(self) -> List[GitHubEvent]:
        """
        Extract data and convert to strongly-typed model objects.
        
        Returns:
            List of GitHubEvent model instances
        """
        file_path = self.extract()
        raw_events = self.repository.load_events(file_path)
        
        # Convert to model objects
        events = []
        for raw_event in raw_events:
            try:
                event = GitHubEvent.from_dict(raw_event)
                events.append(event)
            except (ValueError, KeyError) as e:
                logger.warning(f"Failed to parse event: {e}")
                continue
        
        return events
