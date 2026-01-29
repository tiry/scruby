# Step 5: Preprocessor Components

**Status**: ✅ Complete  
**Related Spec**: `specs/00-implementation-plan.md`

---

## Goals

1. Create abstract `Preprocessor` base class
2. Implement preprocessor registry using ComponentRegistry
3. Create default preprocessing implementations:
   - `WhitespaceNormalizer` - normalize whitespace
   - `TextCleaner` - remove extra spaces, normalize line breaks
4. Support chaining multiple preprocessors
5. Implement comprehensive unit tests

---

## Architecture Overview

Preprocessors transform document content before it's passed to the redactor. They operate on documents and return modified versions.

### Input/Output Format

Preprocessors receive and return documents as Python dictionaries:

```python
{"content": "text content", "metadata": {...}}
```

---

## Implementation Details

### Directory Structure

```
src/scruby/preprocessors/
├── __init__.py          # Expose public API
├── base.py              # Abstract Preprocessor base class
├── registry.py          # Preprocessor registry instance
├── whitespace.py        # WhitespaceNormalizer implementation
└── text_cleaner.py      # TextCleaner implementation

tests/
└── test_preprocessors.py  # Preprocessor tests
```

---

## base.py - Abstract Preprocessor Class

### API Design

```python
"""Abstract base class for preprocessors."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class Preprocessor(ABC):
    """
    Abstract base class for document preprocessors.
    
    All preprocessors must implement the process() method.
    """
    
    @abstractmethod
    def process(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a document.
        
        Args:
            document: Document dictionary with 'content' and optional 'metadata'
            
        Returns:
            Processed document with modified content
            
        Raises:
            PreprocessorError: If processing fails
        """
        pass


class PreprocessorError(Exception):
    """Raised when a preprocessor encounters an error."""
    pass
```

---

## registry.py - Preprocessor Registry

```python
"""Registry for preprocessor components."""

from scruby.registry import ComponentRegistry

# Create the preprocessor registry instance
preprocessor_registry = ComponentRegistry("preprocessor")


def get_preprocessor_registry() -> ComponentRegistry:
    """Get the preprocessor registry instance."""
    return preprocessor_registry
```

---

## whitespace.py - Whitespace Normalizer

### Features

- Normalize all whitespace to single spaces
- Remove leading/trailing whitespace
- Convert multiple spaces to single space
- Normalize line breaks

### API Design

```python
"""Whitespace normalization preprocessor."""

import re
from typing import Any, Dict

from .base import Preprocessor, PreprocessorError
from .registry import preprocessor_registry


@preprocessor_registry.register_decorator("whitespace_normalizer")
class WhitespaceNormalizer(Preprocessor):
    """
    Normalizes whitespace in documents.
    
    - Converts tabs to spaces
    - Converts multiple spaces to single space
    - Removes leading/trailing whitespace from lines
    - Normalizes line breaks to \n
    """
    
    def __init__(self, preserve_paragraphs: bool = True):
        """
        Initialize the whitespace normalizer.
        
        Args:
            preserve_paragraphs: If True, preserve paragraph breaks (double newlines)
        """
        self.preserve_paragraphs = preserve_paragraphs
    
    def process(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize whitespace in document.
        
        Args:
            document: Document with 'content' key
            
        Returns:
            Document with normalized content
            
        Raises:
            PreprocessorError: If processing fails
        """
        if "content" not in document:
            raise PreprocessorError("Document must contain 'content' key")
        
        try:
            content = document["content"]
            
            # Convert tabs to spaces
            content = content.replace("\t", " ")
            
            # Normalize line breaks
            content = content.replace("\r\n", "\n").replace("\r", "\n")
            
            if self.preserve_paragraphs:
                # Preserve double newlines (paragraph breaks)
                # Replace 2+ newlines with placeholder
                content = re.sub(r"\n\n+", "<<<PARAGRAPH>>>", content)
                # Remove multiple spaces
                content = re.sub(r" +", " ", content)
                # Restore paragraph breaks
                content = content.replace("<<<PARAGRAPH>>>", "\n\n")
            else:
                # Replace all whitespace sequences with single space
                content = re.sub(r"\s+", " ", content)
            
            # Strip leading/trailing whitespace
            content = content.strip()
            
            # Return modified document
            return {
                **document,
                "content": content
            }
        except Exception as e:
            raise PreprocessorError(f"Failed to normalize whitespace: {e}") from e
```

---

## text_cleaner.py - Text Cleaner

### Features

- Remove extra punctuation
- Normalize quotes
- Remove control characters
- Optional lowercasing

### API Design

```python
"""Text cleaning preprocessor."""

import re
from typing import Any, Dict

from .base import Preprocessor, PreprocessorError
from .registry import preprocessor_registry


@preprocessor_registry.register_decorator("text_cleaner")
class TextCleaner(Preprocessor):
    """
    Cleans and normalizes text content.
    
    - Removes control characters
    - Normalizes quotes
    - Optionally converts to lowercase
    - Removes multiple punctuation
    """
    
    def __init__(self, lowercase: bool = False, normalize_quotes: bool = True):
        """
        Initialize the text cleaner.
        
        Args:
            lowercase: If True, convert text to lowercase
            normalize_quotes: If True, normalize curly quotes to straight quotes
        """
        self.lowercase = lowercase
        self.normalize_quotes = normalize_quotes
    
    def process(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean text in document.
        
        Args:
            document: Document with 'content' key
            
        Returns:
            Document with cleaned content
            
        Raises:
            PreprocessorError: If processing fails
        """
        if "content" not in document:
            raise PreprocessorError("Document must contain 'content' key")
        
        try:
            content = document["content"]
            
            # Remove control characters (except newlines and tabs)
            content = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", content)
            
            if self.normalize_quotes:
                # Normalize curly quotes to straight quotes
                content = content.replace(""", '"').replace(""", '"')
                content = content.replace("'", "'").replace("'", "'")
            
            if self.lowercase:
                content = content.lower()
            
            # Remove multiple punctuation (e.g., "!!!" -> "!")
            content = re.sub(r"([!?.])\1+", r"\1", content)
            
            # Return modified document
            return {
                **document,
                "content": content
            }
        except Exception as e:
            raise PreprocessorError(f"Failed to clean text: {e}") from e
```

---

## __init__.py - Public API

```python
"""Preprocessor components for scruby."""

from .base import Preprocessor, PreprocessorError
from .registry import get_preprocessor_registry, preprocessor_registry
from .text_cleaner import TextCleaner
from .whitespace import WhitespaceNormalizer

__all__ = [
    "Preprocessor",
    "PreprocessorError",
    "preprocessor_registry",
    "get_preprocessor_registry",
    "WhitespaceNormalizer",
    "TextCleaner",
]
```

---

## Unit Tests

### Test Coverage (`tests/test_preprocessors.py`)

**Test Base Class:**
1. `test_preprocessor_is_abstract` - Verify Preprocessor cannot be instantiated
2. `test_preprocessor_requires_process_method` - Verify subclass must implement process()

**Test Registry:**
3. `test_preprocessor_registry_exists` - Verify registry is available
4. `test_whitespace_normalizer_registered` - Verify WhitespaceNormalizer auto-registered
5. `test_text_cleaner_registered` - Verify TextCleaner auto-registered
6. `test_create_preprocessor_from_registry` - Create preprocessor via factory

**Test WhitespaceNormalizer:**
7. `test_normalize_tabs_to_spaces` - Convert tabs to spaces
8. `test_normalize_multiple_spaces` - Convert multiple spaces to single
9. `test_normalize_line_breaks` - Normalize different line break types
10. `test_preserve_paragraphs` - Keep paragraph breaks when enabled
11. `test_dont_preserve_paragraphs` - Remove all extra whitespace when disabled
12. `test_strip_leading_trailing` - Remove leading/trailing whitespace

**Test TextCleaner:**
13. `test_remove_control_characters` - Remove control characters
14. `test_normalize_quotes` - Convert curly quotes to straight
15. `test_lowercase_conversion` - Convert to lowercase when enabled
16. `test_no_lowercase_conversion` - Keep case when disabled
17. `test_normalize_multiple_punctuation` - Reduce repeated punctuation

**Test Error Handling:**
18. `test_missing_content_key` - Handle document without content
19. `test_preprocessor_chaining` - Chain multiple preprocessors

---

## Usage Examples

### Single Preprocessor

```python
from scruby.preprocessors import WhitespaceNormalizer

preprocessor = WhitespaceNormalizer()
document = {"content": "Hello    world\t\twith   spaces"}

result = preprocessor.process(document)
print(result["content"])  # "Hello world with spaces"
```

### Chaining Preprocessors

```python
from scruby.preprocessors import WhitespaceNormalizer, TextCleaner

doc = {"content": "Hello   "World"!!!"}

# First normalize whitespace
doc = WhitespaceNormalizer().process(doc)
# Then clean text
doc = TextCleaner(normalize_quotes=True).process(doc)

print(doc["content"])  # 'Hello "World"!'
```

### Via Registry

```python
from scruby.preprocessors import preprocessor_registry

preprocessor = preprocessor_registry.create("whitespace_normalizer")
result = preprocessor.process(document)
```

---

## Success Criteria

- ✅ `Preprocessor` abstract base class defined
- ✅ `PreprocessorError` exception defined
- ✅ `preprocessor_registry` instance created and exported
- ✅ `WhitespaceNormalizer` implemented with full functionality
- ✅ `TextCleaner` implemented
- ✅ Preprocessors auto-registered with decorators
- ✅ All unit tests pass
- ✅ Test coverage >90% for preprocessors package
- ✅ Support for chaining preprocessors
- ✅ Documents maintain metadata through processing

---

## Next Step

After completing Step 5, proceed to:
**Step 6: Presidio Configuration & Custom Recognizers** (`specs/06-presidio-configuration.md`)
