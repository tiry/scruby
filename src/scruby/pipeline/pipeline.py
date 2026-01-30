"""Document redaction pipeline orchestrator."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from scruby.config import load_config
from scruby.postprocessors import get_postprocessor_registry
from scruby.preprocessors import get_preprocessor_registry
from scruby.readers import get_reader_registry
from scruby.redactor import Redactor
from scruby.writers import get_writer_registry


class Pipeline:
    """
    Orchestrates the complete document redaction workflow.
    
    Flow: Reader → Preprocessors → Redactor → Postprocessors → Writer
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the pipeline.
        
        Args:
            config: Configuration dictionary (loads from file if None)
        """
        self.config = config or load_config()
        
        # Initialize registries
        self.reader_registry = get_reader_registry()
        self.preprocessor_registry = get_preprocessor_registry()
        self.postprocessor_registry = get_postprocessor_registry()
        self.writer_registry = get_writer_registry()
        
        # Initialize redactor
        self.redactor = Redactor(config=self.config)
    
    def process(
        self,
        input_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        reader_type: str = "text_file",
        writer_type: str = "text_file",
        preprocessors: Optional[List[str]] = None,
        postprocessors: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Process documents through the complete redaction pipeline.
        
        Each document is processed through the entire pipeline (preprocess,
        redact, postprocess, write) before moving to the next document.
        This streaming approach is more memory-efficient for large datasets.
        
        Args:
            input_path: Path to input file or directory
            output_path: Path for output (file/directory/None for stdout)
            reader_type: Type of reader to use
            writer_type: Type of writer to use
            preprocessors: List of preprocessor names to apply
            postprocessors: List of postprocessor names to apply
            
        Returns:
            List of processed documents with metadata
            
        Raises:
            PipelineError: If processing fails
        """
        try:
            # Initialize reader and writer once
            reader = self._create_reader(input_path, reader_type)
            writer = self._create_writer(output_path, writer_type)
            
            # Process each document through complete pipeline
            processed_documents = []
            
            for document in reader.read():
                # Process single document through pipeline
                doc = self._preprocess_document(document, preprocessors)
                
                # Check if this is structured data with field-level redaction
                selected_for_redaction = doc.get("metadata", {}).get("selected_for_redaction")
                
                if selected_for_redaction:
                    # Structured data path: redact each field individually
                    doc = self._redact_fields(doc)
                else:
                    # Normal path: redact content string
                    doc = self.redactor.redact(doc)
                
                doc = self._postprocess_document(doc, postprocessors)
                
                # Write immediately
                writer.write(doc)
                
                # Store for return value
                processed_documents.append(doc)
            
            # Close writer to ensure all data is flushed to disk
            if hasattr(writer, 'close'):
                writer.close()
            
            return processed_documents
            
        except Exception as e:
            raise PipelineError(f"Pipeline processing failed: {e}") from e
    
    def _create_reader(
        self,
        input_path: Union[str, Path],
        reader_type: str
    ):
        """Create and return a reader instance."""
        return self.reader_registry.create(reader_type, path=input_path)
    
    def _preprocess_document(
        self,
        document: Dict[str, Any],
        preprocessor_names: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Apply preprocessors to a single document."""
        if not preprocessor_names:
            return document
        
        doc = document
        for name in preprocessor_names:
            # Only pass config to preprocessors that accept it (field_selector)
            if name == "field_selector":
                preprocessor = self.preprocessor_registry.create(name, config=self.config)
            else:
                preprocessor = self.preprocessor_registry.create(name)
            doc = preprocessor.process(doc)
        
        return doc
    
    
    def _redact_fields(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Redact structured data fields individually.
        
        For structured data with selected_for_redaction metadata,
        this redacts each field separately and stores results in
        redacted_fields metadata.
        
        Args:
            document: Document with selected_for_redaction in metadata
            
        Returns:
            Document with redacted_fields in metadata
        """
        selected_for_redaction = document.get("metadata", {}).get("selected_for_redaction", {})
        
        if not selected_for_redaction:
            return document
        
        # Redact each field individually
        redacted_fields = {}
        total_entities = 0
        
        for field, value in selected_for_redaction.items():
            # Create temp document for this field
            field_doc = {
                "content": str(value),
                "metadata": {}
            }
            
            # Redact the field
            redacted_doc = self.redactor.redact(field_doc)
            
            # Store redacted value
            redacted_fields[field] = redacted_doc["content"]
            
            # Accumulate entity count
            total_entities += redacted_doc.get("metadata", {}).get("redacted_entities", 0)
        
        # Store results in document metadata
        document["metadata"]["redacted_fields"] = redacted_fields
        document["metadata"]["redacted_entities"] = total_entities
        
        return document
    
    def _postprocess_document(
        self,
        document: Dict[str, Any],
        postprocessor_names: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Apply postprocessors to a single document."""
        if not postprocessor_names:
            return document
        
        doc = document
        for name in postprocessor_names:
            # Only pass config to postprocessors that accept it (dict_merger)
            if name == "dict_merger":
                postprocessor = self.postprocessor_registry.create(name, config=self.config)
            else:
                postprocessor = self.postprocessor_registry.create(name)
            doc = postprocessor.process(doc)
        
        return doc
    
    def _create_writer(
        self,
        output_path: Optional[Union[str, Path]],
        writer_type: str
    ):
        """
        Create and return a writer instance.
        
        Args:
            output_path: Path for output (file/directory/None for stdout)
            writer_type: Type of writer to use
            
        Returns:
            Writer instance
            
        Raises:
            PipelineError: If writer creation fails
        """
        # Handle specific writer types
        if writer_type == "stdout":
            return self.writer_registry.create(writer_type)
        
        if writer_type == "text_file" and output_path is None:
            raise PipelineError("output_path is required for text_file writer")
        
        # For all other writers, try to create with path if provided
        if output_path is not None:
            return self.writer_registry.create(writer_type, path=output_path)
        else:
            return self.writer_registry.create(writer_type)


class PipelineError(Exception):
    """Raised when pipeline processing fails."""
    pass
