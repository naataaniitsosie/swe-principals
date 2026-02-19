"""
Configuration for GHArchive data extraction.
Repositories match CONFORMITY.md "Repositories Under Investigation".
"""
from dataclasses import dataclass
from typing import List
from datetime import datetime

from dataset_readers.config import RepositoryConfig


@dataclass
class ExtractionConfig:
    """Configuration for GHArchive extraction. Raw: filter by repo and event type; preprocessor does the rest."""
    repositories: List[RepositoryConfig]
    start_date: datetime
    end_date: datetime
    event_types: List[str]
    output_dir: str = "./data/raw"

    def __post_init__(self):
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        if not self.repositories:
            raise ValueError("repositories cannot be empty")
        if not self.event_types:
            raise ValueError("event_types cannot be empty")


# Repositories under investigation (CONFORMITY.md). Use exact owner/repo for GHArchive filter.
REPOSITORIES: List[RepositoryConfig] = [
    RepositoryConfig(owner="expressjs", name="express"),
    RepositoryConfig(owner="nestjs", name="nest"),
    RepositoryConfig(owner="koajs", name="koa"),
    RepositoryConfig(owner="fastify", name="fastify"),
    RepositoryConfig(owner="hapijs", name="hapi"),
    RepositoryConfig(owner="spring-projects", name="spring-boot"),
    RepositoryConfig(owner="tiangolo", name="fastapi"),
    RepositoryConfig(owner="django", name="django"),
    RepositoryConfig(owner="pallets", name="flask"),
    RepositoryConfig(owner="gin-gonic", name="gin"),
]

DEFAULT_EVENT_TYPES = [
    "PullRequestEvent",
    "PullRequestReviewEvent",
    "PullRequestReviewCommentEvent",
    "IssueCommentEvent",
]
