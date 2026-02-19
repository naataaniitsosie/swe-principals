"""
Abstract base class for dataset readers.
Strategy pattern: each reader implements extraction for a specific data source.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List


class DatasetReaderBase(ABC):
    """
    Abstract base class for dataset readers.
    Readers extract GitHub PR/event data from different sources (GHArchive, BigQuery, etc.).
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier (e.g. 'gharchive', 'bigquery')."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of the data source."""
        pass

    @abstractmethod
    def extract(self, **kwargs: Any):
        """
        Execute extraction. Returns path to saved data file, or list of (repo_full_name, path)
        when extracting multiple repositories.
        """
        pass
