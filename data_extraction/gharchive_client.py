"""
Client for interacting with GHArchive API.
Follows Single Responsibility Principle - only handles HTTP requests to GHArchive.
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
    """Abstract base class for HTTP clients. Follows Dependency Inversion Principle."""
    
    @abstractmethod
    def get(self, url: str, **kwargs) -> requests.Response:
        """Perform GET request."""
        pass


class RequestsHTTPClient(HTTPClient):
    """Concrete implementation using requests library."""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
    
    def get(self, url: str, **kwargs) -> requests.Response:
        """Perform GET request with timeout."""
        kwargs.setdefault('timeout', self.timeout)
        return self.session.get(url, **kwargs)
    
    def close(self):
        """Close the session."""
        self.session.close()


class GHArchiveClient:
    """
    Client for fetching data from GHArchive.
    Handles URL construction, data fetching, and decompression.
    """
    
    BASE_URL = "https://data.gharchive.org"
    
    def __init__(self, http_client: HTTPClient):
        """
        Initialize with dependency injection of HTTP client.
        Follows Dependency Inversion Principle.
        """
        self.http_client = http_client
    
    def _construct_url(self, date: datetime, hour: int) -> str:
        """Construct GHArchive URL for specific date and hour."""
        return f"{self.BASE_URL}/{date.year}-{date.month:02d}-{date.day:02d}-{hour}.json.gz"
    
    def fetch_hour_data(self, date: datetime, hour: int) -> List[Dict[str, Any]]:
        """
        Fetch and decompress GHArchive data for a specific hour.
        
        Args:
            date: The date to fetch data for
            hour: The hour (0-23) to fetch data for
            
        Returns:
            List of event dictionaries
            
        Raises:
            requests.RequestException: If the HTTP request fails
        """
        url = self._construct_url(date, hour)
        logger.info(f"Fetching data from {url}")
        
        try:
            response = self.http_client.get(url, stream=True)
            response.raise_for_status()
            
            # Decompress and parse JSON lines
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
    
    def fetch_date_range(self, start_date: datetime, end_date: datetime) -> Iterator[List[Dict[str, Any]]]:
        """
        Fetch data for a date range, yielding hourly batches.
        
        Args:
            start_date: Start date (inclusive)
            end_date: End date (exclusive)
            
        Yields:
            Lists of event dictionaries for each hour
        """
        current_date = start_date
        
        while current_date < end_date:
            for hour in range(24):
                # Check if we've passed the end date
                current_datetime = current_date.replace(hour=hour)
                if current_datetime >= end_date:
                    return
                
                try:
                    events = self.fetch_hour_data(current_date, hour)
                    if events:
                        yield events
                except requests.RequestException:
                    # Log error and continue with next hour
                    logger.warning(f"Skipping {current_date.date()} hour {hour} due to fetch error")
                    continue
            
            current_date += timedelta(days=1)
