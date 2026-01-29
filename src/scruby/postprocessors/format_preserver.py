"""Postprocessor to preserve document formatting."""

from typing import Any, Dict

from .base import Postprocessor
from .registry import postprocessor_registry


@postprocessor_registry.register_decorator("format_preserver")
class FormatPreserver(Postprocessor):
    """
    Preserves document formatting after redaction.
    
    - Maintains paragraph breaks
    - Preserves line structure
    """
    
    def __init__(self, preserve_paragraphs: bool = True):
        """
        Initialize the formatter.
        
        Args:
            preserve_paragraphs: Whether to preserve paragraph breaks
        """
        self.preserve_paragraphs = preserve_paragraphs
    
    def process(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Preserve document formatting.
        
        Args:
            document: Document with redacted content
            
        Returns:
            Document with preserved formatting
        """
        content = document["content"]
        
        if self.preserve_paragraphs:
            # Preserve paragraph breaks (double newlines)
            # Simply ensure content structure is maintained
            pass
        
        return {
            **document,
            "content": content
        }
