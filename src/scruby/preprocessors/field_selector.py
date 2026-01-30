"""Field selector preprocessor for structured data."""

from typing import Dict, Any, List

from .base import Preprocessor
from .registry import preprocessor_registry


@preprocessor_registry.register_decorator("field_selector")
class FieldSelectorPreprocessor(Preprocessor):
    """
    Preprocessor that selects specific fields from structured data for redaction.
    
    Instead of concatenating fields into a content string, this preprocessor
    simply extracts the selected fields into metadata for field-by-field redaction
    by the pipeline.
    
    Input document structure:
        {
            "content": None,
            "metadata": {
                "original_data": {"field1": "value1", "field2": "value2", ...}
            }
        }
    
    Output document structure:
        {
            "content": None,  # NOT USED for structured data
            "metadata": {
                "original_data": {...},
                "selected_for_redaction": {"field1": "value1", ...},
                "selected_fields": ["field1", ...]
            }
        }
    """
    
    def __init__(self, config: Dict[str, Any] | None = None):
        """
        Initialize field selector.
        
        Args:
            config: Configuration dictionary
        """
        # Get field selector config
        selector_config = {}
        if config:
            selector_config = config.get("preprocessors", {}).get("field_selector", {})
        
        self.fields: List[str] = selector_config.get("fields", [])
    
    def process(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process document by selecting fields for redaction.
        
        Args:
            document: Document with original_data in metadata
            
        Returns:
            Document with selected_for_redaction in metadata
        """
        # Get original data from metadata
        original_data = document.get("metadata", {}).get("original_data", {})
        
        if not original_data:
            # No structured data to process
            return document
        
        if not self.fields:
            # No fields configured, select all fields
           selected_fields = list(original_data.keys())
        else:
            # Select only configured fields that exist
            selected_fields = [f for f in self.fields if f in original_data]
        
        # Extract selected fields into separate dict
        selected_for_redaction = {
            field: original_data[field]
            for field in selected_fields
            if field in original_data
        }
        
        # Update document metadata
        if "metadata" not in document:
            document["metadata"] = {}
        
        document["metadata"]["selected_for_redaction"] = selected_for_redaction
        document["metadata"]["selected_fields"] = selected_fields
        
        # Keep content as None for structured data
        # (pipeline will detect selected_for_redaction and process fields individually)
        document["content"] = None
        
        return document
