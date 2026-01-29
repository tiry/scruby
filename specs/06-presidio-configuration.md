# Step 6: Presidio Configuration & Custom Recognizers

**Status**: ✅ Complete  
**Related Spec**: `specs/00-implementation-plan.md`

---

## Goals

1. Install and configure Microsoft Presidio analyzer
2. Create custom HIPAA-compliant recognizers
3. Implement recognizer registry for extensibility
4. Build analyzer wrapper with configuration support
5. Implement comprehensive unit tests

---

## Architecture Overview

This step integrates Microsoft Presidio for PII detection with custom recognizers tailored for HIPAA compliance. The analyzer identifies sensitive information in documents before redaction.

### Key Components

- **Presidio Analyzer Wrapper**: Simplified interface to Presidio
- **Custom Recognizers**: HIPAA-specific entity recognizers
- **Recognizer Registry**: Pluggable recognizer system
- **Configuration Integration**: Uses existing config.py

---

## Implementation Details

### Directory Structure

```
src/scruby/presidio/
├── __init__.py              # Expose public API
├── analyzer_wrapper.py      # Presidio analyzer wrapper
├── custom_recognizers.py    # HIPAA custom recognizers
└── recognizer_registry.py   # Recognizer registration system

tests/
└── test_presidio.py         # Presidio integration tests
```

---

## Dependencies

Add to `pyproject.toml`:

```toml
dependencies = [
    "presidio-analyzer>=2.2.0",
    "spacy>=3.7.0",
]
```

Note: Presidio requires a spaCy model. We'll use `en_core_web_lg` for production.

---

## analyzer_wrapper.py - Presidio Analyzer Wrapper

### Features

- Wraps Presidio AnalyzerEngine with simplified API
- Loads configuration from config.yaml
- Supports custom recognizers
- Configurable confidence threshold
- Entity filtering based on config

### API Design

```python
"""Presidio analyzer wrapper."""

from typing import Any, Dict, List, Optional

from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_analyzer.nlp_engine import NlpEngineProvider

from scruby.config import load_config
from .recognizer_registry import get_recognizer_registry


class PresidioAnalyzer:
    """
    Wrapper around Presidio AnalyzerEngine with custom configuration.
    
    Integrates custom recognizers and configuration from config.yaml.
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        language: str = "en"
    ):
        """
        Initialize Presidio analyzer.
        
        Args:
            config: Configuration dictionary (loads from file if None)
            language: Language for NLP processing
        """
        self.config = config or load_config()
        self.language = language
        
        # Create NLP engine provider
        nlp_config = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": language, "model_name": "en_core_web_lg"}]
        }
        provider = NlpEngineProvider(nlp_configuration=nlp_config)
        nlp_engine = provider.create_engine()
        
        # Create analyzer with custom recognizers
        self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
        
        # Register custom recognizers
        self._register_custom_recognizers()
    
    def _register_custom_recognizers(self) -> None:
        """Register custom recognizers from the registry."""
        registry = get_recognizer_registry()
        for recognizer in registry.get_all_recognizers():
            self.analyzer.registry.add_recognizer(recognizer)
    
    def analyze(
        self,
        text: str,
        entities: Optional[List[str]] = None,
        language: Optional[str] = None
    ) -> List[RecognizerResult]:
        """
        Analyze text for PII entities.
        
        Args:
            text: Text to analyze
            entities: List of entity types to detect (uses config if None)
            language: Language override
            
        Returns:
            List of RecognizerResult objects
        """
        # Use configured entities if not specified
        if entities is None:
            entities = self.config.get("entities_to_redact", [])
        
        # Get confidence threshold from config
        score_threshold = self.config.get(
            "presidio_confidence_threshold",
            0.5
        )
        
        # Analyze text
        results = self.analyzer.analyze(
            text=text,
            entities=entities,
            language=language or self.language,
            score_threshold=score_threshold
        )
        
        return results
    
    def get_supported_entities(self) -> List[str]:
        """Get list of all supported entity types."""
        return self.analyzer.get_supported_entities(language=self.language)


class PresidioAnalyzerError(Exception):
    """Raised when Presidio analyzer encounters an error."""
    pass
```

---

## custom_recognizers.py - HIPAA Custom Recognizers

### Custom Recognizers

1. **MRN (Medical Record Number)**: Pattern-based recognizer
2. **PRESCRIPTION_NUMBER**: Alphanumeric prescription IDs
3. **INSURANCE_ID**: Health insurance identification numbers

### API Design

```python
"""Custom recognizers for HIPAA compliance."""

import re
from typing import List, Optional

from presidio_analyzer import Pattern, PatternRecognizer


class MRNRecognizer(PatternRecognizer):
    """
    Recognizer for Medical Record Numbers (MRN).
    
    Detects common MRN formats:
    - MRN: 12345678
    - MRN-12345678
    - Medical Record: 12345678
    """
    
    PATTERNS = [
        Pattern(
            name="mrn_with_prefix",
            regex=r"\bMRN[:\-\s]?\d{6,10}\b",
            score=0.85
        ),
        Pattern(
            name="medical_record_with_prefix",
            regex=r"\bMedical\s+Record[:\-\s]?\d{6,10}\b",
            score=0.85
        ),
    ]
    
    def __init__(self):
        super().__init__(
            supported_entity="MEDICAL_RECORD_NUMBER",
            patterns=self.PATTERNS,
            context=["patient", "medical", "record", "chart"]
        )


class PrescriptionNumberRecognizer(PatternRecognizer):
    """
    Recognizer for prescription numbers.
    
    Detects formats like:
    - RX: 1234567
    - Prescription #1234567
    """
    
    PATTERNS = [
        Pattern(
            name="rx_with_prefix",
            regex=r"\bRX[:\-\s#]?\d{6,10}\b",
            score=0.80
        ),
        Pattern(
            name="prescription_with_prefix",
            regex=r"\bPrescription\s+[#:\-\s]?\d{6,10}\b",
            score=0.80
        ),
    ]
    
    def __init__(self):
        super().__init__(
            supported_entity="PRESCRIPTION_NUMBER",
            patterns=self.PATTERNS,
            context=["prescription", "medication", "pharmacy", "drug"]
        )


class InsuranceIDRecognizer(PatternRecognizer):
    """
    Recognizer for health insurance ID numbers.
    
    Detects formats like:
    - Insurance ID: ABC123456789
    - Member ID: 123456789
    """
    
    PATTERNS = [
        Pattern(
            name="insurance_id",
            regex=r"\b(?:Insurance|Member)\s+ID[:\-\s]?[A-Z0-9]{9,15}\b",
            score=0.75
        ),
        Pattern(
            name="policy_number",
            regex=r"\bPolicy\s+(?:Number|#)[:\-\s]?[A-Z0-9]{9,15}\b",
            score=0.75
        ),
    ]
    
    def __init__(self):
        super().__init__(
            supported_entity="INSURANCE_ID",
            patterns=self.PATTERNS,
            context=["insurance", "policy", "coverage", "member"]
        )
```

---

## recognizer_registry.py - Recognizer Registry

### Features

- Central registry for all recognizers (built-in + custom)
- Easy registration and retrieval
- Singleton pattern for global access

### API Design

```python
"""Registry for Presidio recognizers."""

from typing import List

from presidio_analyzer import EntityRecognizer

from .custom_recognizers import (
    MRNRecognizer,
    PrescriptionNumberRecognizer,
    InsuranceIDRecognizer,
)


class RecognizerRegistry:
    """
    Registry for managing Presidio recognizers.
    
    Maintains a collection of custom recognizers that can be
    added to the Presidio analyzer.
    """
    
    def __init__(self):
        """Initialize the registry with default custom recognizers."""
        self._recognizers: List[EntityRecognizer] = []
        self._register_defaults()
    
    def _register_defaults(self) -> None:
        """Register default custom recognizers."""
        self.add_recognizer(MRNRecognizer())
        self.add_recognizer(PrescriptionNumberRecognizer())
        self.add_recognizer(InsuranceIDRecognizer())
    
    def add_recognizer(self, recognizer: EntityRecognizer) -> None:
        """
        Add a recognizer to the registry.
        
        Args:
            recognizer: EntityRecognizer instance to add
        """
        self._recognizers.append(recognizer)
    
    def get_all_recognizers(self) -> List[EntityRecognizer]:
        """Get all registered recognizers."""
        return self._recognizers.copy()
    
    def clear(self) -> None:
        """Clear all recognizers from the registry."""
        self._recognizers.clear()


# Singleton instance
_recognizer_registry = RecognizerRegistry()


def get_recognizer_registry() -> RecognizerRegistry:
    """Get the global recognizer registry instance."""
    return _recognizer_registry
```

---

## __init__.py - Public API

```python
"""Presidio integration for scruby."""

from .analyzer_wrapper import PresidioAnalyzer, PresidioAnalyzerError
from .custom_recognizers import (
    InsuranceIDRecognizer,
    MRNRecognizer,
    PrescriptionNumberRecognizer,
)
from .recognizer_registry import RecognizerRegistry, get_recognizer_registry

__all__ = [
    "PresidioAnalyzer",
    "PresidioAnalyzerError",
    "MRNRecognizer",
    "PrescriptionNumberRecognizer",
    "InsuranceIDRecognizer",
    "RecognizerRegistry",
    "get_recognizer_registry",
]
```

---

## Unit Tests

### Test Coverage (`tests/test_presidio.py`)

**Test Analyzer Wrapper:**
1. `test_analyzer_initialization` - Verify analyzer initializes correctly
2. `test_analyze_with_builtin_entities` - Detect built-in entities (PERSON, EMAIL, etc.)
3. `test_analyze_with_custom_entities` - Detect custom HIPAA entities
4. `test_analyze_with_config` - Use configuration from config.yaml
5. `test_confidence_threshold` - Respect confidence threshold setting
6. `test_get_supported_entities` - List all supported entity types

**Test Custom Recognizers:**
7. `test_mrn_recognizer` - Detect medical record numbers
8. `test_mrn_various_formats` - Handle different MRN formats
9. `test_prescription_recognizer` - Detect prescription numbers
10. `test_insurance_id_recognizer` - Detect insurance IDs
11. `test_recognizer_context` - Verify context improves detection

**Test Recognizer Registry:**
12. `test_registry_defaults` - Verify default recognizers are registered
13. `test_add_custom_recognizer` - Add new recognizer to registry
14. `test_get_all_recognizers` - Retrieve all registered recognizers
15. `test_registry_clear` - Clear registry

---

## Installation Steps

1. Update `pyproject.toml` with Presidio dependencies
2. Install dependencies: `pip install -e .`
3. Download spaCy model: `python -m spacy download en_core_web_lg`

---

## Success Criteria

- ✅ Presidio analyzer wrapper implemented
- ✅ Three custom HIPAA recognizers created (MRN, Prescription, Insurance)
- ✅ Recognizer registry system functional
- ✅ Integration with existing config.py
- ✅ All unit tests pass
- ✅ spaCy model downloaded and working
- ✅ Analyzer detects both built-in and custom entities

---

## Next Step

After completing Step 6, proceed to:
**Step 7: Redactor Component** (`specs/07-redactor-component.md`)
