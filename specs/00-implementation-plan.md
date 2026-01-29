# Scruby Implementation Plan

## Overview

This document outlines the step-by-step implementation plan for the **scruby** CLI tool - a Python-based text redaction tool that removes HIPAA PII identifiers using Microsoft Presidio.

## Technical Stack

- **Python**: 3.11+
- **CLI Framework**: Click
- **PII Detection**: Microsoft Presidio (presidio-analyzer, presidio-anonymizer)
- **NLP Model**: spaCy with en_core_web_lg
- **Configuration**: YAML (PyYAML)
- **Testing**: pytest with pytest-cov
- **Project Structure**: src/ layout with venv

## Architecture Principles

All pipeline components follow a **pluggable architecture**:
- Abstract base classes define interfaces
- Registry pattern for component discovery
- Factory pattern for component instantiation
- Easy extensibility for new implementations

## Implementation Steps

### Step 1: Project Setup & Configuration
**Spec**: `specs/01-project-setup-configuration.md`

**Goals**:
- Set up Python venv
- Create project structure (src/ layout)
- Define `pyproject.toml` with dependencies
- Implement configuration loading (`config.py`)
- Create default `config.yaml`

**Tests**:
- Config loading and validation
- Default values
- Error handling for missing/invalid config

---

### Step 2: Registry & Factory Pattern
**Spec**: `specs/02-registry-factory-pattern.md`

**Goals**:
- Create base registry system
- Implement factory pattern for component creation
- Provide foundation for all pluggable components

**Tests**:
- Component registration
- Component retrieval
- Factory instantiation
- Error handling for unknown components

---

### Step 3: Reader Components
**Spec**: `specs/03-reader-components.md`

**Goals**:
- Abstract `Reader` base class
- Reader registry and factory
- Default text file reader (single file + folder support)
- Return format: `{"content": "..."}`

**Tests**:
- Single file reading
- Folder reading
- Error handling
- Registry and factory operations

---

### Step 4: Writer Components
**Spec**: `specs/04-writer-components.md`

**Goals**:
- Abstract `Writer` base class
- Writer registry and factory
- Text file writer (single file + folder)
- Stdout writer (for --out not specified)

**Tests**:
- File writing
- Folder writing
- Stdout writing
- Registry and factory operations

---

### Step 5: Preprocessor Components
**Spec**: `specs/05-preprocessor-components.md`

**Goals**:
- Abstract `Preprocessor` base class
- Preprocessor registry and factory
- Identity preprocessor (extract fields to redact)
- Support for simple text format

**Tests**:
- Field extraction
- Empty document handling
- Registry and factory operations

---

### Step 6: Presidio Configuration & Custom Recognizers
**Spec**: `specs/06-presidio-configuration.md`

**Goals**:
- Configure Presidio for all 18 HIPAA PII identifiers
- Implement custom `PatternRecognizer` for:
  - Medical Record Number (MRN)
  - Health Plan Beneficiary Numbers
  - Certificate/License Numbers
  - Vehicle Identification Numbers (VIN)
- Set up `AnalyzerEngine` with all recognizers
- Configure `AnonymizerEngine` with HMAC operators

**Tests**:
- Custom recognizer pattern matching
- Analyzer engine configuration
- Anonymizer operator setup
- All 18 HIPAA identifiers

---

### Step 7: Redactor Component
**Spec**: `specs/07-redactor-component.md`

**Goals**:
- Abstract `Redactor` base class
- Redactor registry and factory
- Presidio-based redactor implementation:
  - Entity detection via Presidio
  - Entity normalization (trim, lowercase, ASCII)
  - HMAC-SHA1 hashing with configurable salt
  - Format: `<entity_type>:<hash>`
  - Overlapping span handling
  - Confidence threshold filtering

**Tests**:
- Simple PII redaction (names, emails)
- Phone numbers, SSNs
- Custom entities (MRN, VIN)
- Normalization consistency
- HMAC consistency (same entity = same hash)
- Overlapping entities
- Confidence threshold
- All 18 HIPAA identifiers

---

### Step 8: Postprocessor Components
**Spec**: `specs/08-postprocessor-components.md`

**Goals**:
- Abstract `Postprocessor` base class
- Postprocessor registry and factory
- Identity postprocessor (merge redacted fields back)

**Tests**:
- Field merging
- Multiple field handling
- Registry and factory operations

---

### Step 9: Pipeline Orchestrator
**Spec**: `specs/09-pipeline-orchestrator.md`

**Goals**:
- Coordinate full pipeline:
  1. READ → 2. PRE-PROCESS → 3. REDACT → 4. POST-PROCESS → 5. SAVE
- Support `--max` parameter
- Support `--dry-run` mode
- Track entity statistics for `--log-stats`

**Tests**:
- End-to-end pipeline
- Dry-run mode
- Max file limit
- Statistics tracking
- Error handling

---

### Step 10: CLI Implementation
**Spec**: `specs/10-cli-implementation.md`

**Goals**:
- Click-based CLI with all parameters:
  - `--reader` (default: "text_file")
  - `--writer` (default: auto-detect based on --out)
  - `--src` (required)
  - `--out` (optional, stdout if not provided)
  - `--config` (default: "config.yaml")
  - `--max` (default: -1)
  - `--dry-run` (flag)
  - `--threshold` (override config)
  - `--log-stats` (CSV output path)
- Entry point configuration in `pyproject.toml`

**Tests**:
- Basic invocation
- All parameter combinations
- Stdout output
- Dry-run flag
- Statistics logging
- Error handling

---

### Step 11: Integration Testing
**Spec**: `specs/11-integration-testing.md`

**Goals**:
- Comprehensive integration tests with realistic data
- Test all 18 HIPAA identifiers
- Test multiple files
- Test hash consistency across documents

**Tests**:
- Full HIPAA coverage
- Multiple file processing
- Cross-document consistency
- Custom recognizers in realistic scenarios

---

### Step 12: Documentation
**Spec**: `specs/12-documentation.md`

**Goals**:
- Comprehensive `README.md`:
  - Project description
  - Installation instructions (venv, dependencies, spaCy model)
  - Usage examples
  - Configuration guide
  - Architecture overview
  - Testing instructions
- Keep documentation updated throughout implementation

---

## Testing Strategy

### Test-Driven Development
- Write tests alongside or before implementation
- Target >90% code coverage
- Use `pytest` with `pytest-cov`

### Test Organization
```
tests/
├── fixtures/           # Sample data and configs
├── test_config.py
├── test_registry.py
├── test_readers.py
├── test_writers.py
├── test_preprocessors.py
├── test_presidio_config.py
├── test_redactors.py
├── test_postprocessors.py
├── test_pipeline.py
├── test_cli.py
└── test_integration.py
```

### Test Fixtures
- Sample text files with various PII types
- Test configuration files
- Mock Presidio components where appropriate
- Real spaCy model for integration tests

---

## Success Criteria

- ✅ All 18 HIPAA PII identifiers detected and redacted
- ✅ Consistent HMAC hashing (same entity = same hash)
- ✅ All components properly registered and pluggable
- ✅ >90% unit test coverage
- ✅ CLI fully functional with all options
- ✅ Documentation complete and up-to-date
- ✅ spaCy en_core_web_lg model integrated
- ✅ Custom recognizers working for non-standard identifiers

---

## 18 HIPAA PII Identifiers

The tool must detect and redact all of the following:

1. **Names** - Patient names, family members, employers
2. **Geographic subdivisions** - Smaller than state (cities, counties, zip codes)
3. **Dates** - Birth dates, admission dates, discharge dates, death dates (except year)
4. **Telephone numbers**
5. **Fax numbers**
6. **Email addresses**
7. **Social Security numbers**
8. **Medical record numbers (MRN)** - *Custom recognizer*
9. **Health plan beneficiary numbers** - *Custom recognizer*
10. **Account numbers**
11. **Certificate/License numbers** - *Custom recognizer*
12. **Vehicle identifiers (VIN)** - *Custom recognizer*
13. **Device identifiers and serial numbers**
14. **URLs**
15. **IP addresses**
16. **Biometric identifiers**
17. **Full-face photos and comparable images**
18. **Any other unique identifying number, characteristic, or code**

---

## Next Steps

1. Create detailed spec for Step 1 (`specs/01-project-setup-configuration.md`)
2. Implement Step 1 with tests
3. Update this plan as needed based on discoveries
4. Proceed sequentially through Steps 2-12
