"""
Configuration module for GHArchive data extraction.
Centralized configuration following Single Responsibility Principle.
"""
from dataclasses import dataclass
from typing import List
from datetime import datetime


@dataclass
class RepositoryConfig:
    """Configuration for target repository."""
    owner: str
    name: str
    
    @property
    def full_name(self) -> str:
        """Returns the full repository name in owner/repo format."""
        return f"{self.owner}/{self.name}"


@dataclass
class ExtractionConfig:
    """Configuration for data extraction process."""
    repository: RepositoryConfig
    start_date: datetime
    end_date: datetime
    event_types: List[str]
    output_dir: str = "./data/raw"
    
    def __post_init__(self):
        """Validate configuration after initialization."""
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        
        if not self.event_types:
            raise ValueError("event_types cannot be empty")


# Default configuration for ExpressJS
EXPRESSJS_CONFIG = ExtractionConfig(
    repository=RepositoryConfig(owner="expressjs", name="express"),
    start_date=datetime(2023, 1, 1),  # Configurable date range
    end_date=datetime(2024, 12, 31),
    event_types=["PullRequestEvent", "PullRequestReviewEvent", "PullRequestReviewCommentEvent", "IssueCommentEvent"]
)
