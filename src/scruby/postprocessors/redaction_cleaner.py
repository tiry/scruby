"""Postprocessor to clean up redaction artifacts."""

import re
from typing import Any, Dict

from .base import Postprocessor
from .registry import get_postprocessor_registry


class RedactionCleaner(Postprocessor):
    """
    Cleans up redaction artifacts.
    
    - Merges consecutive [REDACTED] tokens
    - Removes extra spaces around redactions
    - Normalizes punctuation after redactions
    """
    
    def __init__(self, merge_consecutive: bool = True):
        """
        Initialize the cleaner.
        
        Args:
            merge_consecutive: Whether to merge consecutive redactions
        """
        self.merge_consecutive = merge_consecutive
    
    def process(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean up redaction artifacts.
        
        Args:
            document: Document with redacted content
            
        Returns:
            Document with cleaned content
        """
        content = document["content"]
        
        if self.merge_consecutive:
            # Merge consecutive [REDACTED] tokens
            content = re.sub(r'(\[REDACTED\]\s*)+', '[REDACTED] ', content)
        
        # Clean up extra spaces
        content = re.sub(r'\s+', ' ', content)
        content = content.strip()
        
        # Fix punctuation spacing
        content = re.sub(r'\s+([.,!?;:])', r'\1', content)
        
        return {
            **document,
            "content": content
        }
