"""
Filters for processing GitHub events.
Uses Strategy Pattern for flexible filtering logic.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
from data_extraction.models import GitHubEvent, EventType


class EventFilter(ABC):
    """Abstract base class for event filters. Follows Open/Closed Principle."""
    
    @abstractmethod
    def matches(self, event: Dict[str, Any]) -> bool:
        """Check if event matches filter criteria."""
        pass


class RepositoryFilter(EventFilter):
    """Filter events by repository name."""
    
    def __init__(self, repo_full_name: str):
        """
        Args:
            repo_full_name: Repository name in 'owner/repo' format
        """
        self.repo_full_name = repo_full_name.lower()
    
    def matches(self, event: Dict[str, Any]) -> bool:
        """Check if event is from the target repository."""
        repo_name = event.get('repo', {}).get('name', '').lower()
        return repo_name == self.repo_full_name


class EventTypeFilter(EventFilter):
    """Filter events by type."""
    
    def __init__(self, event_types: List[str]):
        """
        Args:
            event_types: List of event type strings to match
        """
        self.event_types = set(event_types)
    
    def matches(self, event: Dict[str, Any]) -> bool:
        """Check if event type is in the allowed list."""
        event_type = event.get('type', '')
        return event_type in self.event_types


class CompositeFilter(EventFilter):
    """
    Combines multiple filters with AND logic.
    Follows Composite Pattern.
    """
    
    def __init__(self, filters: List[EventFilter]):
        """
        Args:
            filters: List of filters to apply
        """
        self.filters = filters
    
    def matches(self, event: Dict[str, Any]) -> bool:
        """Check if event matches all filters."""
        return all(f.matches(event) for f in self.filters)
    
    def add_filter(self, filter: EventFilter):
        """Add a new filter to the composite."""
        self.filters.append(filter)


class HasTextContentFilter(EventFilter):
    """Filter events that contain text content suitable for sentiment analysis."""
    
    def matches(self, event: Dict[str, Any]) -> bool:
        """Check if event has meaningful text content."""
        try:
            gh_event = GitHubEvent.from_dict(event)
            text = gh_event.extract_text_content()
            return text is not None and len(text.strip()) > 0
        except (ValueError, KeyError):
            return False


class EventFilterPipeline:
    """
    Pipeline for filtering events through multiple filters.
    Encapsulates filtering logic and provides clean interface.
    """
    
    def __init__(self, filter: EventFilter):
        """
        Args:
            filter: The filter (simple or composite) to apply
        """
        self.filter = filter
        self.stats = {'total': 0, 'matched': 0, 'filtered': 0}
    
    def filter_events(self, events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Filter a list of events.
        
        Args:
            events: List of event dictionaries
            
        Returns:
            Filtered list of events
        """
        matched_events = []
        
        for event in events:
            self.stats['total'] += 1
            
            if self.filter.matches(event):
                matched_events.append(event)
                self.stats['matched'] += 1
            else:
                self.stats['filtered'] += 1
        
        return matched_events
    
    def get_stats(self) -> Dict[str, int]:
        """Get filtering statistics."""
        return self.stats.copy()
    
    def reset_stats(self):
        """Reset statistics counters."""
        self.stats = {'total': 0, 'matched': 0, 'filtered': 0}
