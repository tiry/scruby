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
            # Step 1: Read documents
            documents = self._read_documents(input_path, reader_type)
            
            # Step 2: Preprocess documents
            documents = self._preprocess_documents(documents, preprocessors)
            
            # Step 3: Redact PII
            documents = self._redact_documents(documents)
            
            # Step 4: Postprocess documents
            documents = self._postprocess_documents(documents, postprocessors)
            
            # Step 5: Write documents
            self._write_documents(documents, output_path, writer_type)
            
            return documents
            
        except Exception as e:
            raise PipelineError(f"Pipeline processing failed: {e}") from e
    
    def _read_documents(
        self,
        input_path: Union[str, Path],
        reader_type: str
    ) -> List[Dict[str, Any]]:
        """Read documents using specified reader."""
        reader = self.reader_registry.create(reader_type, path=input_path)
        # Convert iterator to list
        documents = list(reader.read())
        
        return documents
    
    def _preprocess_documents(
        self,
        documents: List[Dict[str, Any]],
        preprocessor_names: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Apply preprocessors to documents."""
        if not preprocessor_names:
            return documents
        
        processed = []
        for doc in documents:
            for name in preprocessor_names:
                preprocessor = self.preprocessor_registry.create(name)
                doc = preprocessor.process(doc)
            processed.append(doc)
        
        return processed
    
    def _redact_documents(
        self,
        documents: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Redact PII from documents."""
        redacted = []
        for doc in documents:
            redacted_doc = self.redactor.redact(doc)
            redacted.append(redacted_doc)
        
        return redacted
    
    def _postprocess_documents(
        self,
        documents: List[Dict[str, Any]],
        postprocessor_names: Optional[List[str]]
    ) -> List[Dict[str, Any]]:
        """Apply postprocessors to documents."""
        if not postprocessor_names:
            return documents
        
        processed = []
        for doc in documents:
            for name in postprocessor_names:
                postprocessor = self.postprocessor_registry.create(name)
                doc = postprocessor.process(doc)
            processed.append(doc)
        
        return processed
    
    def _write_documents(
        self,
        documents: List[Dict[str, Any]],
        output_path: Optional[Union[str, Path]],
        writer_type: str
    ) -> None:
        """Write documents using specified writer."""
        # Create writer with appropriate parameters
        if writer_type == "text_file":
            if output_path is None:
                raise PipelineError("output_path is required for text_file writer")
            writer = self.writer_registry.create(writer_type, path=output_path)
        elif writer_type == "stdout":
            writer = self.writer_registry.create(writer_type)
        else:
            # For extensibility: try to create with path if provided
            if output_path is not None:
                writer = self.writer_registry.create(writer_type, path=output_path)
            else:
                writer = self.writer_registry.create(writer_type)
        
        for doc in documents:
            writer.write(doc)


class PipelineError(Exception):
    """Raised when pipeline processing fails."""
    pass
