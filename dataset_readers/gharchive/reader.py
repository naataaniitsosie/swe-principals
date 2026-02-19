"""
GHArchive dataset reader. Wraps DataExtractor for the dataset_readers plugin interface.
Fetches each hour once; one SQLite DB for all configured repos.
"""
from datetime import datetime
from typing import Any, List, Tuple

from dataset_readers.base import DatasetReaderBase
from dataset_readers.config import RepositoryConfig
from dataset_readers.registry import register_reader
from dataset_readers.gharchive.config import ExtractionConfig, DEFAULT_EVENT_TYPES
from dataset_readers.gharchive.extractor import DataExtractor

try:
    from project_config import DATA_DIR
except ImportError:
    raise ImportError("project_config.py is required to set DATA_DIR")

@register_reader("gharchive")
class GHArchiveReader(DatasetReaderBase):
    """Reads GitHub events from GHArchive (data.gharchive.org)."""

    name = "gharchive"
    description = "GitHub events from GHArchive (static hourly files)"

    def __init__(
        self,
        repositories: List[RepositoryConfig],
        start_date: datetime,
        end_date: datetime,
        event_types: List[str] = None,
        **kwargs: Any,
    ):
        if event_types is None:
            event_types = DEFAULT_EVENT_TYPES
        config = ExtractionConfig(
            repositories=repositories,
            start_date=start_date,
            end_date=end_date,
            event_types=event_types,
            output_dir=str(DATA_DIR),
        )
        self._extractor = DataExtractor(config)

    def extract(self, **kwargs: Any) -> List[Tuple[str, str]]:
        """Returns list of (repo_full_name, db_path). Same db_path for all repos."""
        return self._extractor.extract()
