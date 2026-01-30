"""Dictionary merger postprocessor for structured data."""

from typing import Dict, Any

from .base import Postprocessor
from .registry import postprocessor_registry


@postprocessor_registry.register_decorator("dict_merger")
class DictMergerPostprocessor(Postprocessor):
    """
    Postprocessor that merges preserved and redacted fields.
    
    Takes documents with:
    - original_data (all fields from source)
    - selected_fields (which fields were redacted)
    - redacted_fields (redacted values for selected fields)
    
    Produces:
    - redacted_data (complete dict with preserved + redacted fields)
    
    Example:
        Input:
            original_data: {ID: "1", Name: "John", Email: "john@x.com"}
            selected_fields: ["Name", "Email"]
            redacted_fields: {"Name": "<PERSON:abc>", "Email": "<EMAIL:def>"}
        
        Output:
            redacted_data: {ID: "1", Name: "<PERSON:abc>", Email: "<EMAIL:def>"}
    """
    
    def __init__(self, config: Dict[str,Any] | None = None):
        """
        Initialize dict merger.
        
        Args:
            config: Configuration dictionary
        """
        # Get config if needed
        merger_config = {}
        if config:
            merger_config = config.get("postprocessors", {}).get("dict_merger", {})
        
        self.preserve_unselected = merger_config.get("preserve_unselected", True)
    
    def process(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process document by merging preserved and redacted fields.
        
        Args:
            document: Document with redacted_fields in metadata
            
        Returns:
            Document with redacted_data in metadata
        """
        metadata = document.get("metadata", {})
        
        # Get components
        original_data = metadata.get("original_data", {})
        selected_fields = metadata.get("selected_fields", [])
        redacted_fields = metadata.get("redacted_fields", {})
        
        if not redacted_fields:
            # No structured data to merge
            return document
        
        # Start with original data (all fields)
        if self.preserve_unselected:
            redacted_data = original_data.copy()
        else:
            # Only include selected fields
            redacted_data = {}
        
        # Replace selected fields with redacted values
        for field in selected_fields:
            if field in redacted_fields:
                redacted_data[field] = redacted_fields[field]
        
        # Store result in metadata
        document["metadata"]["redacted_data"] = redacted_data
        
        return document
