"""Abstract base class for readers."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator


class Reader(ABC):
    """
    Abstract base class for document readers.

    All readers must implement the read() method that returns an iterator
    of document dictionaries.
    """

    @abstractmethod
    def read(self) -> Iterator[Dict[str, Any]]:
        """
        Read documents from the source.

        Yields:
            Document dictionaries with at least a 'content' key

        Raises:
            ReaderError: If reading fails
        """
        pass


class ReaderError(Exception):
    """Raised when a reader encounters an error."""

    pass
