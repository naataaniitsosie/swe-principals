"""
Storage layer for extracted GHArchive events.
Supports one-shot save (full list) and streaming append (bounded memory).
"""
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class StreamingWriter:
    """
    Writes events to a JSONL file by appending; keeps only a file handle and count in memory.
    Call append_events() per batch, then finalize() to write metadata and close.
    """

    def __init__(self, base_dir: Path, metadata: Dict[str, Any]):
        self._metadata = dict(metadata)
        self._base_dir = base_dir
        self._base_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        repo_name = self._metadata.get("repository", "unknown").replace("/", "_")
        self._filename = f"{repo_name}_{timestamp}.jsonl"
        self._path = self._base_dir / self._filename
        self._file = open(self._path, "w", encoding="utf-8")
        self._count = 0

    def append_events(self, events: List[Dict[str, Any]]) -> None:
        for item in events:
            json.dump(item, self._file, ensure_ascii=False)
            self._file.write("\n")
        self._count += len(events)

    def finalize(self, additional_metadata: Optional[Dict[str, Any]] = None) -> str:
        self._file.close()
        self._metadata["record_count"] = self._count
        self._metadata["saved_at"] = datetime.now().isoformat()
        self._metadata["file_path"] = str(self._path)
        if additional_metadata:
            self._metadata.update(additional_metadata)
        metadata_path = self._base_dir / f"{self._filename}.meta.json"
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(self._metadata, f, indent=2, ensure_ascii=False)
        logger.info("Saved %s records to %s", self._count, self._path)
        return str(self._path)

    @property
    def path(self) -> Path:
        return self._path

    @property
    def count(self) -> int:
        return self._count


class DataStorage(ABC):
    """Abstract base for data storage."""

    @abstractmethod
    def save(self, data: List[Dict[str, Any]], metadata: Dict[str, Any]) -> str:
        pass

    @abstractmethod
    def load(self, identifier: str) -> List[Dict[str, Any]]:
        pass


class JSONLinesStorage(DataStorage):
    """Storage using JSON Lines format."""

    def __init__(self, base_dir: str):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _generate_filename(self, metadata: Dict[str, Any]) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        repo_name = metadata.get("repository", "unknown").replace("/", "_")
        return f"{repo_name}_{timestamp}.jsonl"

    def save(self, data: List[Dict[str, Any]], metadata: Dict[str, Any]) -> str:
        filename = self._generate_filename(metadata)
        data_path = self.base_dir / filename
        metadata_path = self.base_dir / f"{filename}.meta.json"

        with open(data_path, "w", encoding="utf-8") as f:
            for item in data:
                json.dump(item, f, ensure_ascii=False)
                f.write("\n")

        metadata["record_count"] = len(data)
        metadata["saved_at"] = datetime.now().isoformat()
        metadata["file_path"] = str(data_path)

        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved {len(data)} records to {data_path}")
        return str(data_path)

    def load(self, identifier: str) -> List[Dict[str, Any]]:
        path = Path(identifier)
        if not path.exists():
            raise FileNotFoundError(f"Data file not found: {identifier}")

        data = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    data.append(json.loads(line))

        logger.info(f"Loaded {len(data)} records from {identifier}")
        return data

    def create_writer(self, metadata: Dict[str, Any]) -> StreamingWriter:
        """Create a streaming writer that appends events; use finalize() when done."""
        return StreamingWriter(self.base_dir, metadata)


class DataRepository:
    """High-level repository for storage operations."""

    def __init__(self, storage: DataStorage):
        self.storage = storage

    def save_extracted_events(
        self,
        events: List[Dict[str, Any]],
        repository: str,
        start_date: datetime,
        end_date: datetime,
        additional_metadata: Dict[str, Any] = None,
    ) -> str:
        metadata = {
            "repository": repository,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "extraction_date": datetime.now().isoformat(),
        }
        if additional_metadata:
            metadata.update(additional_metadata)
        return self.storage.save(events, metadata)

    def create_extraction_writer(
        self,
        repository: str,
        start_date: datetime,
        end_date: datetime,
    ) -> StreamingWriter:
        """Create a streaming writer for one repo. Append events per batch, then call finalize()."""
        metadata = {
            "repository": repository,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "extraction_date": datetime.now().isoformat(),
        }
        return self.storage.create_writer(metadata)

    def load_events(self, identifier: str) -> List[Dict[str, Any]]:
        return self.storage.load(identifier)
