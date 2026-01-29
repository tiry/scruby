"""Base class for postprocessors."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class Postprocessor(ABC):
    """
    Abstract base class for document postprocessors.
    
    Postprocessors are applied AFTER redaction to clean up
    and format the output.
    """
    
    @abstractmethod
    def process(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a document.
        
        Args:
            document: Document with 'content' and optional 'metadata'
            
        Returns:
            Processed document
        """
        pass
