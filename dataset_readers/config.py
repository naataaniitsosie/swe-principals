"""
Shared configuration for dataset readers.
RepositoryConfig is used by all readers (gharchive, bigquery, etc.).
"""
from dataclasses import dataclass


@dataclass
class RepositoryConfig:
    """Configuration for target repository (owner/name)."""
    owner: str
    name: str

    @property
    def full_name(self) -> str:
        """Returns the full repository name in owner/repo format."""
        return f"{self.owner}/{self.name}"
