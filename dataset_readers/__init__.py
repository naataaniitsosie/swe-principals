"""
Dataset readers package.
Pluggable readers for different GitHub event data sources.

Usage:
    from dataset_readers import get_reader, list_readers

    reader = get_reader("gharchive", repository=..., start_date=..., ...)
    path = reader.extract()
"""
from dataset_readers.base import DatasetReaderBase
from dataset_readers.registry import (
    get_reader,
    get_default_reader_name,
    list_readers,
    register_reader,
)

# Import readers to trigger registration
from dataset_readers import gharchive  # noqa: F401, E402
from dataset_readers import bigquery  # noqa: F401, E402

__all__ = [
    "DatasetReaderBase",
    "get_reader",
    "get_default_reader_name",
    "list_readers",
    "register_reader",
]
