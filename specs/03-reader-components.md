# Step 3: Reader Components

**Status**: ✅ Complete  
**Related Spec**: `specs/00-implementation-plan.md`

---

## Goals

1. Create abstract `Reader` base class
2. Implement reader registry using ComponentRegistry
3. Create `TextFileReader` as default implementation
4. Support reading single files and entire folders
5. Implement comprehensive unit tests

---

## Architecture Overview

Readers are responsible for loading documents from various sources and converting them into a standard Python dictionary format. The default implementation reads text files.

### Output Format

All readers must return documents as Python dictionaries with a `"content"` key:

```python
{"content": "text content of the document"}
```

---

## Implementation Details

### Directory Structure

```
src/scruby/readers/
├── __init__.py       # Expose public API
├── base.py           # Abstract Reader base class
├── registry.py       # Reader registry instance
└── text_file.py      # TextFileReader implementation

tests/
├── test_readers.py   # Reader tests
└── fixtures/
    ├── sample1.txt   # Test file 1
    ├── sample2.txt   # Test file 2
    └── test_folder/  # Test folder with multiple files
        ├── file1.txt
        └── file2.txt
```

---

## base.py - Abstract Reader Class

### API Design

```python
"""Abstract base class for readers."""

from abc import ABC, abstractmethod
from typing import Dict, Iterator, Any


class Reader(ABC):
    """
    Abstract base class for document readers.
    
    All readers must implement the read() method that returns an iterator
    of document dictionaries.
    """
    
    @abstractmethod
    def read(self) -> Iterator[Dict[str, Any]]:
        """
        Read documents from the source.
        
        Yields:
            Document dictionaries with at least a 'content' key
            
        Raises:
            ReaderError: If reading fails
        """
        pass


class ReaderError(Exception):
    """Raised when a reader encounters an error."""
    pass
```

---

## registry.py - Reader Registry

```python
"""Registry for reader components."""

from scruby.registry import ComponentRegistry

# Create the reader registry instance
reader_registry = ComponentRegistry("reader")

# Convenience function to get reader registry
def get_reader_registry() -> ComponentRegistry:
    """Get the reader registry instance."""
    return reader_registry
```

---

## text_file.py - Text File Reader

### Features

- Read single text file
- Read all `.txt` files from a folder
- UTF-8 encoding by default
- Error handling for file not found, permission errors, etc.
- Include filename in document metadata

### API Design

```python
"""Text file reader implementation."""

from pathlib import Path
from typing import Dict, Iterator, Any
import os

from .base import Reader, ReaderError
from .registry import reader_registry


@reader_registry.register_decorator("text_file")
class TextFileReader(Reader):
    """
    Reader for plain text files.
    
    Supports reading a single file or all .txt files in a directory.
    """
    
    def __init__(self, path: str | Path, encoding: str = "utf-8"):
        """
        Initialize the text file reader.
        
        Args:
            path: Path to a file or directory
            encoding: Text encoding (default: utf-8)
        """
        self.path = Path(path)
        self.encoding = encoding
        
        if not self.path.exists():
            raise ReaderError(f"Path not found: {self.path}")
    
    def read(self) -> Iterator[Dict[str, Any]]:
        """
        Read text file(s).
        
        Yields:
            Document dictionaries with 'content' and 'metadata' keys
            
        Raises:
            ReaderError: If reading fails
        """
        if self.path.is_file():
            yield from self._read_file(self.path)
        elif self.path.is_dir():
            yield from self._read_directory(self.path)
        else:
            raise ReaderError(f"Path is neither file nor directory: {self.path}")
    
    def _read_file(self, file_path: Path) -> Iterator[Dict[str, Any]]:
        """Read a single file."""
        try:
            with open(file_path, "r", encoding=self.encoding) as f:
                content = f.read()
            
            yield {
                "content": content,
                "metadata": {
                    "filename": file_path.name,
                    "path": str(file_path.absolute()),
                }
            }
        except Exception as e:
            raise ReaderError(f"Failed to read file {file_path}: {e}") from e
    
    def _read_directory(self, dir_path: Path) -> Iterator[Dict[str, Any]]:
        """Read all .txt files in a directory."""
        txt_files = sorted(dir_path.glob("*.txt"))
        
        if not txt_files:
            raise ReaderError(f"No .txt files found in directory: {dir_path}")
        
        for file_path in txt_files:
            yield from self._read_file(file_path)
```

---

## __init__.py - Public API

```python
"""Reader components for scruby."""

from .base import Reader, ReaderError
from .registry import reader_registry, get_reader_registry
from .text_file import TextFileReader

__all__ = [
    "Reader",
    "ReaderError",
    "reader_registry",
    "get_reader_registry",
    "TextFileReader",
]
```

---

## Unit Tests

### Test Coverage (`tests/test_readers.py`)

**Test Base Class:**
1. `test_reader_is_abstract` - Verify Reader cannot be instantiated
2. `test_reader_requires_read_method` - Verify subclass must implement read()

**Test Registry:**
3. `test_reader_registry_exists` - Verify registry is available
4. `test_text_file_reader_registered` - Verify TextFileReader is auto-registered
5. `test_create_reader_from_registry` - Create reader via factory

**Test TextFileReader - Single File:**
6. `test_read_single_file` - Read a single text file successfully
7. `test_read_single_file_content` - Verify content is correct
8. `test_read_single_file_metadata` - Verify metadata includes filename and path
9. `test_read_nonexistent_file` - Handle missing file with ReaderError
10. `test_read_file_encoding` - Test different text encodings
11. `test_read_file_permission_error` - Handle permission denied errors

**Test TextFileReader - Directory:**
12. `test_read_directory` - Read all .txt files from directory
13. `test_read_directory_multiple_files` - Ver all files are read
14. `test_read_directory_sorted` - Verify files read in sorted order
15. `test_read_directory_no_txt_files` - Handle empty directory with ReaderError
16. `test_read_directory_only_txt` - Verify only .txt files are read (not .md, .py, etc.)

**Test Error Handling:**
17. `test_invalid_path_type` - Handle invalid path types gracefully
18. `test_corrupted_file` - Handle file read errors

---

## Test Fixtures

### fixtures/sample1.txt
```
This is a sample text file for testing.
It contains multiple lines.
```

### fixtures/sample2.txt
```
Another test file.
With different content.
```

### fixtures/test_folder/file1.txt
```
First file in folder.
```

### fixtures/test_folder/file2.txt
```
Second file in folder.
```

---

## Usage Examples

### Read Single File

```python
from scruby.readers import TextFileReader

reader = TextFileReader("input.txt")
for doc in reader.read():
    print(doc["content"])
    print(doc["metadata"]["filename"])
```

### Read Directory

```python
from scruby.readers import TextFileReader

reader = TextFileReader("/data/texts/")
for doc in reader.read():
    print(f"Reading: {doc['metadata']['filename']}")
    process(doc["content"])
```

### Use Registry

```python
from scruby.readers import reader_registry

# Create reader via factory
reader = reader_registry.create("text_file", path="data.txt")
for doc in reader.read():
    print(doc)
```

---

## Success Criteria

- ✅ `Reader` abstract base class defined
- ✅ `ReaderError` exception defined
- ✅ `reader_registry` instance created and exported
- ✅ `TextFileReader` implemented with full functionality
- ✅ TextFileReader auto-registered with decorator
- ✅ All 18 unit tests pass
- ✅ Test coverage >90% for readers package
- ✅ Handles single files and directories correctly
- ✅ Clear error messages for all failure cases
- ✅ Metadata included with each document

---

## Next Step

After completing Step 3, proceed to:
**Step 4: Writer Components** (`specs/04-writer-components.md`)
