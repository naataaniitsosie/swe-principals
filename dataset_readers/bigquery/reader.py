"""
BigQuery dataset reader.
Fetches GitHub events via SQL queries against githubarchive public dataset.
"""
from datetime import datetime
from typing import Any, Dict, List, Tuple

from dataset_readers.base import DatasetReaderBase
from dataset_readers.config import RepositoryConfig
from dataset_readers.registry import register_reader

try:
    from project_config import DATA_DIR
except ImportError:
    raise ImportError("project_config.py is required to set DATA_DIR")


@register_reader("bigquery")
class BigQueryReader(DatasetReaderBase):
    """
    Reads GitHub events from Google BigQuery (githubarchive.day tables).
    Requires google-cloud-bigquery and GCP credentials.
    """

    name = "bigquery"
    description = "GitHub events from BigQuery (githubarchive public dataset)"

    def __init__(
        self,
        repositories: List[RepositoryConfig],
        start_date: datetime,
        end_date: datetime,
        **kwargs: Any,
    ):
        self._repositories = repositories
        self._start_date = start_date
        self._end_date = end_date
        self._output_dir = str(DATA_DIR)

    def extract(self, **kwargs: Any) -> List[Tuple[str, str]]:
        raise NotImplementedError(
            "BigQuery reader not yet implemented. "
            "Install google-cloud-bigquery and configure GCP credentials."
        )
