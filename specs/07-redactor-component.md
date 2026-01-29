# Step 7: Redactor Component

**Status**: ✅ Complete  
**Related Spec**: `specs/00-implementation-plan.md`

---

## Goals

1. Create redactor wrapper around Presidio Anonymizer
2. Support multiple redaction strategies (replace, mask, hash, encrypt)
3. Integrate analyzer and anonymizer seamlessly
4. Preserve document metadata
5. Implement comprehensive unit tests

---

## Architecture Overview

The redactor combines the PresidioAnalyzer (detection) with Presidio Anonymizer (redaction) to process documents and redact sensitive information.

### Key Components

- **Redactor**: Main class that orchestrates analysis and anonymization
- **Redaction Strategies**: Different ways to redact (replace, mask, hash)
- **Configuration Support**: Uses existing config for strategy selection

---

## Implementation Details

### Directory Structure

```
src/scruby/redactor/
├── __init__.py          # Expose public API
└── redactor.py          # Main redactor implementation

tests/
└── test_redactor.py     # Redactor tests
```

---

## redactor.py - Main Redactor

### Features

- Analyzes documents using PresidioAnalyzer
- Redacts detected entities using Presidio Anonymizer
- Supports multiple redaction strategies
- Preserves document metadata
- Configurable via config.yaml

### API Design

```python
"""Document redactor using Presidio."""

from typing import Any, Dict, List, Optional

from presidio_analyzer import RecognizerResult
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from scruby.config import load_config
from scruby.presidio import PresidioAnalyzer


class Redactor:
    """
    Redacts PII from documents using Presidio.
    
    Combines PresidioAnalyzer for detection with AnonymizerEngine
    for redaction.
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        analyzer: Optional[PresidioAnalyzer] = None
    ):
        """
        Initialize the redactor.
        
        Args:
            config: Configuration dictionary (loads from file if None)
            analyzer: Pre-configured PresidioAnalyzer (creates new if None)
        """
        self.config = config or load_config()
        self.analyzer = analyzer or PresidioAnalyzer(config=self.config)
        self.anonymizer = AnonymizerEngine()
    
    def redact(
        self,
        document: Dict[str, Any],
        entities: Optional[List[str]] = None,
        strategy: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Redact PII from a document.
        
        Args:
            document: Document with 'content' and optional 'metadata'
            entities: Entity types to redact (uses config if None)
            strategy: Redaction strategy (uses config if None)
            
        Returns:
            Redacted document with modified content
            
        Raises:
            RedactorError: If redaction fails
        """
        if "content" not in document:
            raise RedactorError("Document must contain 'content' key")
        
        try:
            text = document["content"]
            
            # Analyze text for PII
            results = self.analyzer.analyze(text, entities=entities)
            
            # Get redaction strategy
            if strategy is None:
                if isinstance(self.config, dict):
                    strategy = self.config.get("redaction_strategy", "replace")
                else:
                    strategy = getattr(self.config, "redaction_strategy", "replace")
            
            # Build operators for anonymization
            operators = self._build_operators(strategy)
            
            # Anonymize text
            anonymized = self.anonymizer.anonymize(
                text=text,
                analyzer_results=results,
                operators=operators
            )
            
            # Return redacted document
            return {
                **document,
                "content": anonymized.text,
                "metadata": {
                    **document.get("metadata", {}),
                    "redacted_entities": len(results),
                    "redaction_strategy": strategy
                }
            }
        except Exception as e:
            raise RedactorError(f"Failed to redact document: {e}") from e
    
    def _build_operators(self, strategy: str) -> Dict[str, OperatorConfig]:
        """
        Build operator configuration for anonymization.
        
        Args:
            strategy: Redaction strategy name
            
        Returns:
            Dictionary mapping entity types to operators
        """
        # Map strategy names to Presidio operators
        strategy_map = {
            "replace": {"type": "replace", "new_value": "[REDACTED]"},
            "mask": {"type": "mask", "masking_char": "*", "chars_to_mask": 100, "from_end": False},
            "hash": {"type": "hash"},
            "encrypt": {"type": "encrypt", "key": self._get_encryption_key()},
        }
        
        if strategy not in strategy_map:
            raise RedactorError(f"Unknown redaction strategy: {strategy}")
        
        # Apply strategy to all entity types
        operator_config = strategy_map[strategy]
        return {"DEFAULT": OperatorConfig(**operator_config)}
    
    def _get_encryption_key(self) -> str:
        """Get encryption key from config."""
        if isinstance(self.config, dict):
            key = self.config.get("hmac_secret", "default-key-change-me")
        else:
            key = getattr(self.config, "hmac_secret", "default-key-change-me")
        return key


class RedactorError(Exception):
    """Raised when redaction fails."""
    pass
```

---

## __init__.py - Public API

```python
"""Redactor components for scruby."""

from .redactor import Redactor, RedactorError

__all__ = [
    "Redactor",
    "RedactorError",
]
```

---

## Unit Tests

### Test Coverage (`tests/test_redactor.py`)

**Test Redactor Initialization:**
1. `test_redactor_initialization` - Verify redactor initializes correctly
2. `test_redactor_with_custom_analyzer` - Use pre-configured analyzer
3. `test_redactor_with_config` - Initialize with configuration

**Test Redaction Strategies:**
4. `test_redact_with_replace_strategy` - Replace entities with [REDACTED]
5. `test_redact_with_mask_strategy` - Mask entities with asterisks
6. `test_redact_with_hash_strategy` - Hash entities
7. `test_redact_builtin_entities` - Redact EMAIL, PERSON, etc.
8. `test_redact_custom_entities` - Redact MRN, PRESCRIPTION, etc.

**Test Metadata:**
9. `test_metadata_preserved` - Original metadata preserved
10. `test_metadata_enriched` - Adds redaction info to metadata
11. `test_redacted_entities_count` - Counts redacted entities

**Test Error Handling:**
12. `test_missing_content_key` - Handle document without content
13. `test_invalid_strategy` - Handle unknown redaction strategy
14. `test_redact_empty_document` - Handle empty content

---

## Usage Examples

### Basic Redaction

```python
from scruby.redactor import Redactor

redactor = Redactor()

document = {
    "content": "Contact john.doe@example.com or call 555-1234",
    "metadata": {"source": "email.txt"}
}

result = redactor.redact(document)
print(result["content"])  # "Contact [REDACTED] or call [REDACTED]"
print(result["metadata"]["redacted_entities"])  # 2
```

### Different Strategies

```python
# Replace (default)
result = redactor.redact(document, strategy="replace")
# "Contact [REDACTED] or call [REDACTED]"

# Mask
result = redactor.redact(document, strategy="mask")
# "Contact ********************* or call ********"

# Hash
result = redactor.redact(document, strategy="hash")
# "Contact a1b2c3d4... or call e5f6g7h8..."
```

### Redact Specific Entities

```python
# Only redact emails
result = redactor.redact(document, entities=["EMAIL_ADDRESS"])

# Redact HIPAA entities
medical_doc = {"content": "Patient MRN 12345678 prescribed RX 9876543"}
result = redactor.redact(
    medical_doc,
    entities=["MEDICAL_RECORD_NUMBER", "PRESCRIPTION_NUMBER"]
)
```

---

## Success Criteria

- ✅ Redactor class implemented
- ✅ Integrates PresidioAnalyzer and AnonymizerEngine
- ✅ Multiple redaction strategies supported (replace, mask, hash, encrypt)
- ✅ Metadata preserved and enriched
- ✅ Configuration integration working
- ✅ All unit tests pass
- ✅ Error handling robust

---

## Next Step

After completing Step 7, proceed to:
**Step 8: Postprocessor Components** (`specs/08-postprocessor-components.md`)
