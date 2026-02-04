"""
Read extracted event data for sentiment analysis.
Reuses dataset_readers.gharchive.models for parsing (GitHubEvent, extract_text_content).
"""
import json
import logging
from pathlib import Path
from typing import Iterator, List, Tuple

from dataset_readers.gharchive.models import GitHubEvent

logger = logging.getLogger(__name__)


def _load_jsonl(path: Path) -> Iterator[dict]:
    """Yield one event dict per line from a JSONL file."""
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def load_events_with_text(
    path: str | Path,
) -> Iterator[Tuple[dict, str]]:
    """
    Load events from a JSONL file and yield (raw_event, text) for each event
    that has non-empty text content. Uses GitHubEvent.from_dict and
    extract_text_content() for consistency with dataset extraction.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {path}")

    for raw in _load_jsonl(path):
        try:
            event = GitHubEvent.from_dict(raw)
            text = event.extract_text_content()
            if text and text.strip():
                yield raw, text.strip()
        except (ValueError, KeyError) as e:
            logger.debug("Skip event (parse/text): %s", e)
            continue


def load_events_with_text_from_paths(
    paths: List[str | Path],
) -> Iterator[Tuple[dict, str]]:
    """Yield (raw_event, text) from multiple JSONL files."""
    for p in paths:
        for item in load_events_with_text(p):
            yield item
