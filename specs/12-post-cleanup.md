# Post-Cleanup Improvements

**Date**: January 29, 2026  
**Status**: Completed  
**Test Results**: 186 tests passing, 94% coverage

## Overview

This document describes architectural improvements and bug fixes implemented after the initial project completion. These changes improve code consistency, memory efficiency, test coverage, and fix critical entity detection issues.

---

## 1. Standardized Component Registration

### Problem
Postprocessors were using manual registration in `__init__.py` while all other components (readers, writers, preprocessors) used the cleaner decorator pattern.

### Solution
Migrated postprocessors to use decorator-based registration:

```python
@postprocessor_registry.register_decorator("redaction_cleaner")
class RedactionCleaner(Postprocessor):
    ...
```

### Files Changed
- `src/scruby/postprocessors/redaction_cleaner.py`
- `src/scruby/postprocessors/format_preserver.py`
- `src/scruby/postprocessors/registry.py`
- `src/scruby/postprocessors/__init__.py`

### Benefits
- **Consistency**: All component types now follow the same registration pattern
- **Simplicity**: No manual registration calls needed in `__init__.py`
- **Maintainability**: Easier to add new postprocessors

---

## 2. Refactored Pipeline to Streaming Architecture

### Problem
Pipeline was processing documents in batches:
1. Read ALL documents → 2. Process ALL → 3. Redact ALL → 4. Write ALL

This approach:
- Loads all documents into memory (inefficient for large datasets)
- Delays output until all processing complete
- Cannot handle unlimited document streams

### Solution
Changed to streaming/iterative processing:

```python
for document in reader.read():
    doc = preprocess(document)
    doc = redact(doc)
    doc = postprocess(doc)
    writer.write(doc)  # Write immediately
```

### Files Changed
- `src/scruby/pipeline/pipeline.py`
  - `_read_documents()` → `_create_reader()` (returns iterator, not list)
  - `_preprocess_documents()` → `_preprocess_document()` (single doc)
  - Removed `_redact_documents()` (inline in main loop)
  - `_postprocess_documents()` → `_postprocess_document()` (single doc)
  - `_write_documents()` → `_create_writer()` (returns writer instance)

### Benefits
- **Memory Efficient**: Only one document in memory at a time
- **Faster Initial Output**: First document written before reading second
- **Scalability**: Can process unlimited documents without memory issues
- **Better Error Recovery**: Already-processed documents are written even if processing fails later
- **Code Reduction**: Reduced from 70 to 60 statements (14% reduction)

---

## 3. Snapshot Comparison Test

### Problem
No regression testing to ensure output consistency over time. Changes to redaction logic could break output format without detection.

### Solution
Created comprehensive snapshot test infrastructure:

#### Files Created
1. **`tests/data/snapshot_input.txt`**
   - Sample medical record with various PII types
   - Realistic test case with name, DOB, SSN, MRN, phone, email

2. **`tests/data/snapshot_expected.txt`**
   - Known-good output generated with fixed HMAC key
   - Reference for exact string comparison

3. **`tests/fixtures/snapshot_config.yaml`**
   - Fixed HMAC secret: `"test-snapshot-key-do-not-change"`
   - Ensures deterministic hashing (same input always produces same output)
   - Critical for long-term consistency

4. **`tests/test_integration.py::TestSnapshotComparison`**
   - Processes input through complete pipeline
   - Compares actual output to expected character-by-character
   - Enhanced error messages with unified diff

### Enhanced Error Reporting
When outputs don't match, test shows:
- Unified diff highlighting exactly what changed
- Character counts (expected vs actual)
- Helpful command to update snapshot

Example error output:
```
================================================================================
SNAPSHOT TEST FAILED - Output doesn't match expected!
================================================================================

Unified Diff:
--- expected
+++ actual
@@ -3,7 +3,7 @@
-SSN: 123-45-6789
+SSN: <US_SSN:79c6a0001dd4>

--------------------------------------------------------------------------------

Expected length: 373 chars
Actual length:   374 chars

--------------------------------------------------------------------------------

To update the snapshot, run:
  cp /tmp/snapshot_output.txt tests/data/snapshot_expected.txt
================================================================================
```

### Benefits
- **Regression Detection**: Catches unintended changes to output format
- **Easy Debugging**: Clear diffs show exactly what changed
- **Confidence**: Proves long-term consistency of redaction logic
- **Documentation**: Snapshot files serve as examples of expected output

---

## 4. Fixed SSN Detection Issue

### Problem Discovered
Presidio's built-in `US_SSN` recognizer was not working:
- "SSN: 123-45-6789" → Detected "SSN" as ORGANIZATION
- "123-45-6789" → Detected as DATE_TIME (wrong!)
- Actual SSN number was never redacted

### Root Cause
Presidio's default US_SSN recognizer has insufficient patterns and low confidence scoring.

### Solution
Created custom SSN recognizer with strong regex patterns:

```python
class SSNRecognizer(PatternRecognizer):
    """Recognizer for US Social Security Numbers."""
    
    PATTERNS = [
        Pattern(
            name="ssn_dashes",
            regex=r"\b\d{3}-\d{2}-\d{4}\b",
            score=0.95  # High confidence
        ),
        Pattern(
            name="ssn_spaces",
            regex=r"\b\d{3}\s\d{2}\s\d{4}\b",
            score=0.95
        ),
        Pattern(
            name="ssn_no_separators",
            regex=r"\b\d{9}\b",
            score=0.60  # Lower for less specific pattern
        ),
    ]
```

### Files Changed
- `src/scruby/presidio/custom_recognizers.py` - Added `SSNRecognizer` class
- `src/scruby/presidio/recognizer_registry.py` - Registered SSN recognizer
- `tests/test_presidio.py` - Updated test to expect 4 recognizers (was 3)

### Results
- **Before**: "123-45-6789" → Not redacted or detected as DATE_TIME
- **After**: "123-45-6789" → `<US_SSN:79c6a0001dd4>`

---

## 5. Entity Conflict Resolution

### Problem
When multiple entity types detected for overlapping text spans, all were kept. This caused issues like:
- "SSN: 123-45-6789" → Both "SSN" (ORGANIZATION) and "123-45-6789" (US_SSN) detected
- First match wins, leading to wrong entity being redacted

### Solution
Implemented priority-based conflict resolution in `Redactor._resolve_conflicts()`:

#### Priority System
```python
ENTITY_PRIORITIES = {
    'US_SSN': 100,          # Highest priority
    'EMAIL_ADDRESS': 95,
    'PHONE_NUMBER': 90,
    'CREDIT_CARD': 85,
    'MEDICAL_RECORD_NUMBER': 80,
    'PRESCRIPTION_NUMBER': 75,
    'INSURANCE_ID': 70,
    'PERSON': 60,
    'DATE_TIME': 50,
    'LOCATION': 40,
    'ORGANIZATION': 30,     # Lower priority for generic types
    'DEFAULT': 10
}
```

#### Resolution Algorithm
For overlapping entities, select winner based on:
1. **Entity type priority** (most important)
2. **Confidence score** (from recognizer)
3. **Span length** (tiebreaker)

### Files Changed
- `src/scruby/redactor/redactor.py`
  - Added `_resolve_conflicts()` method
  - Called from `redact()` before anonymization

### Results
- **Before**: "SSN: 123-45-6789" → `<ORGANIZATION:hash>: 123-45-6789` (SSN leaked!)
- **After**: "SSN: 123-45-6789" → `<ORGANIZATION:hash>: <US_SSN:hash>` (both redacted, proper priority)

### Benefits
- **Security**: Ensures high-value PII (SSN, credit cards) always redacted
- **Accuracy**: More specific entity types win over generic ones
- **Robustness**: Handles complex text with overlapping patterns

---

## Test Results

### Coverage
```
Total: 608 statements
Missed: 36 statements
Coverage: 94%
```

### Test Count
- **Total tests**: 186 (185 original + 1 new snapshot test)
- **Passed**: 186
- **Failed**: 0
- **Warnings**: 3 (pytest mark warnings, non-critical)

### Key Test Files
- `tests/test_integration.py::TestSnapshotComparison` - New snapshot test
- `tests/test_presidio.py` - Updated for SSN recognizer
- `tests/test_redactor.py` - All pass with conflict resolution
- `tests/test_pipeline.py` - All pass with streaming architecture

---

## Running the Snapshot Test

```bash
# Run just the snapshot test
pytest tests/test_integration.py::TestSnapshotComparison -v

# Run with keyword matching
pytest -k snapshot -v

# Run all integration tests
pytest tests/test_integration.py -v
```

---

## Future Improvements

1. **Additional Custom Recognizers**
   - Driver's license numbers
   - Passport numbers
   - More healthcare-specific patterns

2. **Configurable Entity Priorities**
   - Allow users to override default priorities
   - Per-entity priority configuration in YAML

3. **Performance Optimization**
   - Cache preprocessor/postprocessor instances
   - Batch processing option for small files

4. **More Snapshot Tests**
   - Different input types (CSV, JSON, etc.)
   - Edge cases (empty files, special characters)
   - Different redaction strategies

---

## References

- **Pipeline Pattern**: [specs/09-pipeline-orchestrator.md](09-pipeline-orchestrator.md)
- **Registry Pattern**: [specs/02-registry-factory-pattern.md](02-registry-factory-pattern.md)
- **Presidio Integration**: [specs/06-presidio-configuration.md](06-presidio-configuration.md)
- **Integration Testing**: [specs/11-integration-testing.md](11-integration-testing.md)
