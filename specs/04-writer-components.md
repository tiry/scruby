# Step 4: Writer Components

**Status**: ✅ Complete  
**Related Spec**: `specs/00-implementation-plan.md`

---

## Goals

1. Create abstract `Writer` base class
2. Implement writer registry using ComponentRegistry
3. Create `TextFileWriter` for writing to files/folders
4. Create `StdoutWriter` for outputting to stdout
5. Implement comprehensive unit tests

---

## Architecture Overview

Writers are responsible for saving processed documents to various destinations. They receive documents in the same dictionary format as readers produce.

### Input Format

All writers must accept documents as Python dictionaries:

```python
{"content": "processed text", "metadata": {"filename": "doc.txt", ...}}
```

---

## Implementation Details

### Directory Structure

```
src/scruby/writers/
├── __init__.py       # Expose public API
├── base.py           # Abstract Writer base class
├── registry.py       # Writer registry instance
├── text_file.py      # TextFileWriter implementation
└── stdout.py         # StdoutWriter implementation

tests/
└── test_writers.py   # Writer tests
```

---

## base.py - Abstract Writer Class

### API Design

```python
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
```

---

## registry.py - Writer Registry

```python
"""Registry for writer components."""

from scruby.registry import ComponentRegistry

# Create the writer registry instance
writer_registry = ComponentRegistry("writer")


def get_writer_registry() -> ComponentRegistry:
    """Get the writer registry instance."""
    return writer_registry
```

---

## text_file.py - Text File Writer

### Features

- Write to a single file
- Write to a folder (using metadata filename)
- UTF-8 encoding by default
- Create directories if they don't exist
- Error handling for permission errors, disk full, etc.

### API Design

```python
"""Text file writer implementation."""

from pathlib import Path
from typing import Any, Dict

from .base import Writer, WriterError
from .registry import writer_registry


@writer_registry.register_decorator("text_file")
class TextFileWriter(Writer):
    """
    Writer for plain text files.
    
    Can write to a single file or to a directory (using document metadata).
    """
    
    def __init__(self, path: str | Path, encoding: str = "utf-8"):
        """
        Initialize the text file writer.
        
        Args:
            path: Path to output file or directory
            encoding: Text encoding (default: utf-8)
        """
        self.path = Path(path)
        self.encoding = encoding
        self.is_directory = False
        
        # Determine if path should be treated as directory
        if self.path.exists() and self.path.is_dir():
            self.is_directory = True
        elif str(self.path).endswith('/'):
            self.is_directory = True
            self.path.mkdir(parents=True, exist_ok=True)
    
    def write(self, document: Dict[str, Any]) -> None:
        """
        Write document to file.
        
        Args:
            document: Document with 'content' and optional 'metadata' keys
            
        Raises:
            WriterError: If writing fails
        """
        if "content" not in document:
            raise WriterError("Document must contain 'content' key")
        
        try:
            if self.is_directory:
                self._write_to_directory(document)
            else:
                self._write_to_file(document)
        except Exception as e:
            raise WriterError(f"Failed to write document: {e}") from e
    
    def _write_to_file(self, document: Dict[str, Any]) -> None:
        """Write to a single file."""
        # Create parent directory if needed
        self.path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(self.path, "w", encoding=self.encoding) as f:
            f.write(document["content"])
    
    def _write_to_directory(self, document: Dict[str, Any]) -> None:
        """Write to directory using filename from metadata."""
        metadata = document.get("metadata", {})
        filename = metadata.get("filename")
        
        if not filename:
            raise WriterError(
                "Document metadata must contain 'filename' when writing to directory"
            )
        
        output_path = self.path / filename
        with open(output_path, "w", encoding=self.encoding) as f:
            f.write(document["content"])
```

---

## stdout.py - Stdout Writer

### Features

- Write content to stdout
- Optional prefix for each document
- Support for metadata display

### API Design

```python
"""Stdout writer implementation."""

import sys
from typing import Any, Dict

from .base import Writer, WriterError
from .registry import writer_registry


@writer_registry.register_decorator("stdout")
class StdoutWriter(Writer):
    """
    Writer that outputs to stdout.
    
    Useful for piping output or when no destination is specified.
    """
    
    def __init__(self, show_metadata: bool = False):
        """
        Initialize stdout writer.
        
        Args:
            show_metadata: If True, display metadata before content
        """
        self.show_metadata = show_metadata
    
    def write(self, document: Dict[str, Any]) -> None:
        """
        Write document to stdout.
        
        Args:
            document: Document with 'content' and optional 'metadata' keys
            
        Raises:
            WriterError: If writing fails
        """
        if "content" not in document:
            raise WriterError("Document must contain 'content' key")
        
        try:
            if self.show_metadata and "metadata" in document:
                metadata = document["metadata"]
                print(f"--- Metadata: {metadata} ---", file=sys.stdout)
            
            print(document["content"], file=sys.stdout)
            
        except Exception as e:
            raise WriterError(f"Failed to write to stdout: {e}") from e
```

---

## __init__.py - Public API

```python
"""Writer components for scruby."""

from .base import Writer, WriterError
from .registry import get_writer_registry, writer_registry
from .stdout import StdoutWriter
from .text_file import TextFileWriter

__all__ = [
    "Writer",
    "WriterError",
    "writer_registry",
    "get_writer_registry",
    "TextFileWriter",
    "StdoutWriter",
]
```

---

## Unit Tests

### Test Coverage (`tests/test_writers.py`)

**Test Base Class:**
1. `test_writer_is_abstract` - Verify Writer cannot be instantiated
2. `test_writer_requires_write_method` - Verify subclass must implement write()

**Test Registry:**
3. `test_writer_registry_exists` - Verify registry is available
4. `test_text_file_writer_registered` - Verify TextFileWriter auto-registered
5. `test_stdout_writer_registered` - Verify StdoutWriter auto-registered
6. `test_create_writer_from_registry` - Create writer via factory

**Test TextFileWriter - Single File:**
7. `test_write_single_file` - Write document to file
8. `test_write_single_file_content` - Verify written content
9. `test_write_creates_directory` - Verify parent dirs created if needed
10. `test_write_overwrites_existing` - Verify file is overwritten

**Test TextFileWriter - Directory:**
11. `test_write_to_directory` - Write multiple documents to folder
12. `test_write_to_directory_uses_metadata_filename` - Verify filename from metadata
13. `test_write_to_directory_missing_filename` - Error if no filename in metadata
14. `test_write_creates_output_directory` - Create directory if doesn't exist

**Test StdoutWriter:**
15. `test_write_to_stdout` - Write to stdout
16. `test_write_to_stdout_with_metadata` - Display metadata when enabled
17. `test_write_to_stdout_captures_output` - Verify output is correct

**Test Error Handling:**
18. `test_write_missing_content_key` - Handle document without content
19. `test_write_permission_error` - Handle write permission errors

---

## Success Criteria

- ✅ `Writer` abstract base class defined
- ✅ `WriterError` exception defined
- ✅ `writer_registry` instance created and exported
- ✅ `TextFileWriter` implemented with full functionality
- ✅ `StdoutWriter` implemented
- ✅ Writers auto-registered with decorators
- ✅ All unit tests pass
- ✅ Test coverage >90% for writers package
- ✅ Clear error messages for all failure cases

---

## Next Step

After completing Step 4, proceed to:
**Step 5: Preprocessor Components** (`specs/05-preprocessor-components.md`)
