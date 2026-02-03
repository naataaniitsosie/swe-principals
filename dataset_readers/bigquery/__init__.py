"""
BigQuery dataset reader.
Fetches GitHub events from Google BigQuery (githubarchive public dataset).
"""
from dataset_readers.bigquery.reader import BigQueryReader

__all__ = ["BigQueryReader"]
