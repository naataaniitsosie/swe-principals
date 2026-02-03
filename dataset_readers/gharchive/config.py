"""
Configuration for GHArchive data extraction.
"""
from dataclasses import dataclass
from typing import List
from datetime import datetime

from dataset_readers.config import RepositoryConfig


@dataclass
class ExtractionConfig:
    """Configuration for GHArchive extraction process."""
    repository: RepositoryConfig
    start_date: datetime
    end_date: datetime
    event_types: List[str]
    output_dir: str = "./data/raw"

    def __post_init__(self):
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        if not self.event_types:
            raise ValueError("event_types cannot be empty")


EXPRESSJS_CONFIG = ExtractionConfig(
    repository=RepositoryConfig(owner="expressjs", name="express"),
    start_date=datetime(2023, 1, 1),
    end_date=datetime(2024, 12, 31),
    event_types=[
        "PullRequestEvent",
        "PullRequestReviewEvent",
        "PullRequestReviewCommentEvent",
        "IssueCommentEvent",
    ],
)
