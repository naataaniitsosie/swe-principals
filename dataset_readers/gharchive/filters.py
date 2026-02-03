"""
Filters for GHArchive events.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List

from dataset_readers.gharchive.models import GitHubEvent, EventType


class EventFilter(ABC):
    """Abstract base for event filters."""

    @abstractmethod
    def matches(self, event: Dict[str, Any]) -> bool:
        pass


class RepositoryFilter(EventFilter):
    """Filter events by repository name."""

    def __init__(self, repo_full_name: str):
        self.repo_full_name = repo_full_name.lower()

    def matches(self, event: Dict[str, Any]) -> bool:
        repo_name = event.get("repo", {}).get("name", "").lower()
        return repo_name == self.repo_full_name


class EventTypeFilter(EventFilter):
    """Filter events by type."""

    def __init__(self, event_types: List[str]):
        self.event_types = set(event_types)

    def matches(self, event: Dict[str, Any]) -> bool:
        return event.get("type", "") in self.event_types


class CompositeFilter(EventFilter):
    """Combines multiple filters with AND logic."""

    def __init__(self, filters: List[EventFilter]):
        self.filters = filters

    def matches(self, event: Dict[str, Any]) -> bool:
        return all(f.matches(event) for f in self.filters)

    def add_filter(self, filter: EventFilter):
        self.filters.append(filter)


class HasTextContentFilter(EventFilter):
    """Filter events with meaningful text for sentiment analysis."""

    def matches(self, event: Dict[str, Any]) -> bool:
        try:
            gh_event = GitHubEvent.from_dict(event)
            text = gh_event.extract_text_content()
            return text is not None and len(text.strip()) > 0
        except (ValueError, KeyError):
            return False


class EventFilterPipeline:
    """Pipeline for filtering events."""

    def __init__(self, filter: EventFilter):
        self.filter = filter
        self.stats = {"total": 0, "matched": 0, "filtered": 0}

    def filter_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        matched_events = []
        for event in events:
            self.stats["total"] += 1
            if self.filter.matches(event):
                matched_events.append(event)
                self.stats["matched"] += 1
            else:
                self.stats["filtered"] += 1
        return matched_events

    def get_stats(self) -> Dict[str, int]:
        return self.stats.copy()

    def reset_stats(self):
        self.stats = {"total": 0, "matched": 0, "filtered": 0}
