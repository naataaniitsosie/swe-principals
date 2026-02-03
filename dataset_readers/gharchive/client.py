"""
Client for GHArchive (data.gharchive.org).
Fetches hourly JSON.gz files.
"""
import gzip
import json
import requests
from datetime import datetime, timedelta
from typing import Iterator, List, Dict, Any
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class HTTPClient(ABC):
    """Abstract base class for HTTP clients."""

    @abstractmethod
    def get(self, url: str, **kwargs) -> requests.Response:
        pass


class RequestsHTTPClient(HTTPClient):
    """Concrete implementation using requests library."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()

    def get(self, url: str, **kwargs) -> requests.Response:
        kwargs.setdefault("timeout", self.timeout)
        return self.session.get(url, **kwargs)

    def close(self):
        self.session.close()


class GHArchiveClient:
    """Client for fetching data from GHArchive."""

    BASE_URL = "https://data.gharchive.org"

    def __init__(self, http_client: HTTPClient):
        self.http_client = http_client

    def _construct_url(self, date: datetime, hour: int) -> str:
        return f"{self.BASE_URL}/{date.year}-{date.month:02d}-{date.day:02d}-{hour}.json.gz"

    def fetch_hour_data(self, date: datetime, hour: int) -> List[Dict[str, Any]]:
        url = self._construct_url(date, hour)
        logger.info(f"Fetching data from {url}")

        try:
            response = self.http_client.get(url, stream=True)
            response.raise_for_status()

            events = []
            with gzip.GzipFile(fileobj=response.raw) as f:
                for line in f:
                    if line.strip():
                        try:
                            events.append(json.loads(line))
                        except json.JSONDecodeError as e:
                            logger.warning(f"Failed to parse JSON line: {e}")
                            continue

            logger.info(f"Fetched {len(events)} events from {url}")
            return events

        except requests.RequestException as e:
            logger.error(f"Failed to fetch data from {url}: {e}")
            raise

    def fetch_date_range(
        self, start_date: datetime, end_date: datetime
    ) -> Iterator[List[Dict[str, Any]]]:
        current_date = start_date

        while current_date < end_date:
            for hour in range(24):
                current_datetime = current_date.replace(hour=hour)
                if current_datetime >= end_date:
                    return

                try:
                    events = self.fetch_hour_data(current_date, hour)
                    if events:
                        yield events
                except requests.RequestException:
                    logger.warning(
                        f"Skipping {current_date.date()} hour {hour} due to fetch error"
                    )
                    continue

            current_date += timedelta(days=1)
