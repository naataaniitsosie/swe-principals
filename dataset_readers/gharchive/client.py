"""
Client for GHArchive (data.gharchive.org).
Fetches hourly JSON.gz files.
"""
import gzip
import json
import requests
from datetime import datetime, timedelta
from typing import Iterator, List, Dict, Any, Optional, Set
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

    def fetch_hour_data(
        self,
        date: datetime,
        hour: int,
        repo_names: Optional[Set[str]] = None,
        event_types: Optional[Set[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch one hour of events. If repo_names/event_types are set, only return events that match both.
        """
        url = self._construct_url(date, hour)

        try:
            response = self.http_client.get(url, stream=True)
            response.raise_for_status()

            events = []
            repo_names_lower = {n.lower() for n in (repo_names or set())}
            event_types_set = event_types or set()
            filter_repo = bool(repo_names_lower)
            filter_type = bool(event_types_set)

            with gzip.GzipFile(fileobj=response.raw) as f:
                for line in f:
                    if not line.strip():
                        continue
                    try:
                        event = json.loads(line)
                    except json.JSONDecodeError as e:
                        logger.warning("Failed to parse JSON line: %s", e)
                        continue
                    if filter_repo:
                        repo_name = (event.get("repo") or {}).get("name") or ""
                        if repo_name.lower() not in repo_names_lower:
                            continue
                    if filter_type and event.get("type") not in event_types_set:
                        continue
                    events.append(event)

            logger.info("Fetched %s events from %s", len(events), url)
            return events

        except requests.RequestException as e:
            logger.error("Failed to fetch data from %s: %s", url, e)
            raise

    def fetch_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        repo_names: Optional[Set[str]] = None,
        event_types: Optional[Set[str]] = None,
    ) -> Iterator[List[Dict[str, Any]]]:
        current_date = start_date

        while current_date < end_date:
            for hour in range(24):
                current_datetime = current_date.replace(hour=hour)
                if current_datetime >= end_date:
                    return

                try:
                    events = self.fetch_hour_data(
                        current_date,
                        hour,
                        repo_names=repo_names,
                        event_types=event_types,
                    )
                    if events:
                        yield events
                except requests.RequestException:
                    logger.warning(
                        "Skipping %s hour %s due to fetch error",
                        current_date.date(),
                        hour,
                    )
                    continue

            current_date += timedelta(days=1)
