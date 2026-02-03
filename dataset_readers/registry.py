"""
Registry for dataset readers.
Plugin pattern: readers register themselves by name.
"""
import logging
from typing import Dict, List, Type, TypeVar

from dataset_readers.base import DatasetReaderBase

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=DatasetReaderBase)
_REGISTRY: Dict[str, Type[DatasetReaderBase]] = {}


def register_reader(name: str) -> type:
    """Decorator to register a DatasetReaderBase subclass."""
    def decorator(cls: Type[T]) -> Type[T]:
        if not issubclass(cls, DatasetReaderBase):
            raise TypeError(f"{cls} must inherit from DatasetReaderBase")
        if name in _REGISTRY:
            logger.warning(f"Overwriting reader '{name}' with {cls.__name__}")
        _REGISTRY[name.lower().strip()] = cls
        return cls
    return decorator


def get_reader(name: str, **kwargs: object) -> DatasetReaderBase:
    """Get an instance of a registered reader by name."""
    key = name.lower().strip()
    if key not in _REGISTRY:
        available = ", ".join(sorted(_REGISTRY.keys()))
        raise KeyError(f"Unknown dataset reader '{name}'. Available: {available}")
    return _REGISTRY[key](**kwargs)


def list_readers() -> List[str]:
    """Return sorted list of registered reader names."""
    return sorted(_REGISTRY.keys())


def get_default_reader_name() -> str:
    """Default reader name (gharchive)."""
    return "gharchive"
