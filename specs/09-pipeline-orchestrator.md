# Step 9: Pipeline Orchestrator

**Status**: Complete  
**Related Spec**: `specs/00-implementation-plan.md`

---

## Goals

1. Create Pipeline class to orchestrate entire document redaction flow
2. Chain all components: Reader → Preprocessors → Redactor → Postprocessors → Writer
3. Support configuration-driven execution
4. Implement error handling and logging
5. Track processing metadata
6. Implement comprehensive unit tests

---

## Architecture Overview

The Pipeline orchestrates the complete document redaction workflow by coordinating all components in the correct order.

### Processing Flow

```
Input → Reader → Preprocessors → Redactor → Postprocessors → Writer → Output
```

### Key Responsibilities

- **Component Initialization**: Create and configure all pipeline components
- **Execution Orchestration**: Execute components in correct order
- **Error Handling**: Gracefully handle failures at each stage
- **Metadata Tracking**: Track processing information throughout pipeline
- **Configuration Management**: Load and apply configuration

---

## Implementation Details

### Directory Structure

```
src/scruby/pipeline/
├── __init__.py          # Expose public API
└── pipeline.py          # Main pipeline implementation

tests/
└── test_pipeline.py     # Pipeline tests
```

---

## pipeline.py - Main Pipeline

```python
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
        reader = self.reader_registry.create(reader_type)
        documents = reader.read(input_path)
        
        # Ensure documents is a list
        if not isinstance(documents, list):
            documents = [documents]
        
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
        writer = self.writer_registry.create(writer_type)
        
        for doc in documents:
            writer.write(doc, output_path)


class PipelineError(Exception):
    """Raised when pipeline processing fails."""
    pass
```

---

## __init__.py - Public API

```python
"""Pipeline orchestrator for scruby."""

from .pipeline import Pipeline, PipelineError

__all__ = [
    "Pipeline",
    "PipelineError",
]
```

---

## Unit Tests

### Test Coverage (`tests/test_pipeline.py`)

**Test Pipeline Initialization:**
1. `test_pipeline_initialization` - Verify pipeline initializes correctly
2. `test_pipeline_with_config` - Initialize with custom config

**Test Complete Pipeline Flow:**
3. `test_process_single_file` - Process single file through pipeline
4. `test_process_with_preprocessors` - Apply preprocessors
5. `test_process_with_postprocessors` - Apply postprocessors
6. `test_process_complete_flow` - Full pipeline with all stages

**Test Component Integration:**
7. `test_reader_integration` - Verify reader works in pipeline
8. `test_redactor_integration` - Verify redactor works in pipeline
9. `test_writer_integration` - Verify writer works in pipeline

**Test Error Handling:**
10. `test_invalid_reader_type` - Handle unknown reader
11. `test_invalid_input_path` - Handle missing input
12. `test_pipeline_error_handling` - Handle processing errors

---

## Usage Examples

### Basic Usage

```python
from scruby.pipeline import Pipeline

pipeline = Pipeline()

# Process a single file
results = pipeline.process(
    input_path="input.txt",
    output_path="output.txt"
)

print(f"Processed {len(results)} documents")
print(f"Redacted {results[0]['metadata']['redacted_entities']} entities")
```

### With Preprocessing and Postprocessing

```python
pipeline = Pipeline()

results = pipeline.process(
    input_path="sensitive_data.txt",
    output_path="redacted_data.txt",
    preprocessors=["whitespace_normalizer", "text_cleaner"],
    postprocessors=["redaction_cleaner", "format_preserver"]
)
```

### Process Directory

```python
# Process all files in a directory
results = pipeline.process(
    input_path="input_dir/",
    output_path="output_dir/"
)

print(f"Processed {len(results)} files")
```

### Output to Stdout

```python
# Write to stdout instead of file
results = pipeline.process(
    input_path="input.txt",
    output_path=None,
    writer_type="stdout"
)
```

---

## Success Criteria

- ✅ Pipeline class implemented
- ✅ Complete workflow orchestration
- ✅ All components integrated correctly
- ✅ Error handling robust
- ✅ Configuration support working
- ✅ Metadata tracked throughout
- ✅ All unit tests pass

---

## Next Step

After completing Step 9, proceed to:
**Step 10: CLI Interface** (`specs/10-cli-interface.md`)
