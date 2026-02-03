"""
GHArchive dataset reader.
Wraps DataExtractor for the dataset_readers plugin interface.
"""
from datetime import datetime
from typing import Any, Dict, List

from dataset_readers.base import DatasetReaderBase
from dataset_readers.config import RepositoryConfig
from dataset_readers.registry import register_reader
from dataset_readers.gharchive.config import ExtractionConfig
from dataset_readers.gharchive.extractor import DataExtractor


@register_reader("gharchive")
class GHArchiveReader(DatasetReaderBase):
    """Reads GitHub events from GHArchive (data.gharchive.org)."""

    name = "gharchive"
    description = "GitHub events from GHArchive (static hourly files)"

    def __init__(
        self,
        repository: RepositoryConfig,
        start_date: datetime,
        end_date: datetime,
        event_types: List[str],
        output_dir: str = "./data/raw",
        **kwargs: Any,
    ):
        config = ExtractionConfig(
            repository=repository,
            start_date=start_date,
            end_date=end_date,
            event_types=event_types,
            output_dir=output_dir,
        )
        self._extractor = DataExtractor(config)

    def extract(self, **kwargs: Any) -> str:
        return self._extractor.extract()

    def load_events(self, file_path: str) -> List[Dict[str, Any]]:
        return self._extractor.repository.load_events(file_path)
