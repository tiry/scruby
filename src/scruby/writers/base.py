"""Abstract base class for writers."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class Writer(ABC):
    """
    Abstract base class for document writers.

    All writers must implement the write() method that saves documents.
    """

    @abstractmethod
    def write(self, document: Dict[str, Any]) -> None:
        """
        Write a document to the destination.

        Args:
            document: Document dictionary with 'content' and optional 'metadata'

        Raises:
            WriterError: If writing fails
        """
        pass


class WriterError(Exception):
    """Raised when a writer encounters an error."""

    pass
