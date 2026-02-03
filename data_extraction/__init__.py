"""
Data extraction package for GHArchive.

This package provides an object-oriented framework for extracting
GitHub event data from GHArchive, with a focus on pull request
sentiment analysis.

Key classes:
    - DataExtractor: Main orchestrator
    - GHArchiveClient: HTTP client for GHArchive API
    - EventFilterPipeline: Filtering logic
    - DataRepository: Storage abstraction
"""
from data_extraction.extractor import DataExtractor
from data_extraction.config import ExtractionConfig, EXPRESSJS_CONFIG
from data_extraction.models import GitHubEvent, EventType

__all__ = [
    'DataExtractor',
    'ExtractionConfig',
    'EXPRESSJS_CONFIG',
    'GitHubEvent',
    'EventType'
]
