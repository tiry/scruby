"""Abstract base class for preprocessors."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class Preprocessor(ABC):
    """
    Abstract base class for document preprocessors.

    All preprocessors must implement the process() method.
    """

    @abstractmethod
    def process(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a document.

        Args:
            document: Document dictionary with 'content' and optional 'metadata'

        Returns:
            Processed document with modified content

        Raises:
            PreprocessorError: If processing fails
        """
        pass


class PreprocessorError(Exception):
    """Raised when a preprocessor encounters an error."""

    pass
