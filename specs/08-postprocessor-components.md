# Step 8: Postprocessor Components

**Status**: ✅ Complete  
**Related Spec**: `specs/00-implementation-plan.md`

---

## Goals

1. Create postprocessor base class and registry (mirror preprocessor architecture)
2. Implement RedactionCleaner to clean up redaction artifacts
3. Implement FormatPreserver to maintain document formatting
4. Ensure postprocessors work with document structure
5. Implement comprehensive unit tests

---

## Architecture Overview

Postprocessors are applied AFTER redaction to clean up and format the output. They follow the same pattern as preprocessors but operate on redacted content.

### Key Components

- **Postprocessor Base Class**: Abstract base for all postprocessors
- **Postprocessor Registry**: Factory pattern for postprocessor management
- **RedactionCleaner**: Cleans up multiple consecutive redactions
- **FormatPreserver**: Preserves whitespace and formatting

---

## Implementation Details

### Directory Structure

```
src/scruby/postprocessors/
├── __init__.py              # Expose public API
├── base.py                  # Abstract base class
├── registry.py              # Postprocessor registry
├── redaction_cleaner.py     # Clean up redactions
└── format_preserver.py      # Preserve formatting

tests/
└── test_postprocessors.py   # Postprocessor tests
```

---

## base.py - Abstract Base Class

```python
"""Base class for postprocessors."""

from abc import ABC, abstractmethod
from typing import Any, Dict


class Postprocessor(ABC):
    """
    Abstract base class for document postprocessors.
    
    Postprocessors are applied AFTER redaction to clean up
    and format the output.
    """
    
    @abstractmethod
    def process(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a document.
        
        Args:
            document: Document with 'content' and optional 'metadata'
            
        Returns:
            Processed document
        """
        pass
```

---

## registry.py - Postprocessor Registry

```python
"""Registry for postprocessors."""

from scruby.registry import ComponentRegistry

# Create postprocessor registry
_postprocessor_registry = ComponentRegistry("postprocessor")


def get_postprocessor_registry() -> ComponentRegistry:
    """Get the global postprocessor registry."""
    return _postprocessor_registry
```

---

## redaction_cleaner.py - Redaction Cleaner

```python
"""Postprocessor to clean up redaction artifacts."""

import re
from typing import Any, Dict

from .base import Postprocessor
from .registry import get_postprocessor_registry


@get_postprocessor_registry().register("redaction_cleaner")
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
```

---

## format_preserver.py - Format Preserver

```python
"""Postprocessor to preserve document formatting."""

from typing import Any, Dict

from .base import Postprocessor
from .registry import get_postprocessor_registry


@get_postprocessor_registry().register("format_preserver")
class FormatPreserver(Postprocessor):
    """
    Preserves document formatting after redaction.
    
    - Maintains paragraph breaks
    - Preserves line structure
    - Keeps indentation (optional)
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
            # Ensure double newlines for paragraph breaks
            lines = content.split('\n')
            formatted_lines = []
            
            for i, line in enumerate(lines):
                formatted_lines.append(line)
                # Add extra newline between non-empty lines for paragraphs
                if i < len(lines) - 1 and line.strip() and lines[i + 1].strip():
                    if '\n\n' not in content[content.find(line):content.find(lines[i + 1])]:
                        formatted_lines.append('')
            
            content = '\n'.join(formatted_lines)
        
        return {
            **document,
            "content": content
        }
```

---

## __init__.py - Public API

```python
"""Postprocessor components for scruby."""

from .base import Postprocessor
from .format_preserver import FormatPreserver
from .redaction_cleaner import RedactionCleaner
from .registry import get_postprocessor_registry

__all__ = [
    "Postprocessor",
    "RedactionCleaner",
    "FormatPreserver",
    "get_postprocessor_registry",
]
```

---

## Unit Tests

### Test Coverage (`tests/test_postprocessors.py`)

**Test Base Class:**
1. `test_postprocessor_is_abstract` - Verify base class is abstract
2. `test_postprocessor_requires_process_method` - Must implement process()

**Test Registry:**
3. `test_postprocessor_registry_exists` - Registry is available
4. `test_redaction_cleaner_registered` - RedactionCleaner is registered
5. `test_format_preserver_registered` - FormatPreserver is registered

**Test RedactionCleaner:**
6. `test_merge_consecutive_redactions` - Merge multiple [REDACTED]
7. `test_clean_extra_spaces` - Remove extra whitespace
8. `test_fix_punctuation_spacing` - Fix spacing around punctuation
9. `test_metadata_preserved` - Original metadata kept

**Test FormatPreserver:**
10. `test_preserve_paragraphs` - Maintain paragraph breaks
11. `test_preserve_line_structure` - Keep line structure
12. `test_metadata_preserved` - Original metadata kept

---

## Success Criteria

- ✅ Postprocessor base class implemented
- ✅ Postprocessor registry functional
- ✅ RedactionCleaner cleans up artifacts
- ✅ FormatPreserver maintains formatting
- ✅ All unit tests pass
- ✅ Integration with document pipeline

---

## Next Step

After completing Step 8, proceed to:
**Step 9: Pipeline Orchestrator** (`specs/09-pipeline-orchestrator.md`)
