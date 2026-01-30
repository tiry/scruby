# Task 13: Structured Data Support (CSV/XLSX)

**Status**: Specification  
**Dependencies**: openpyxl, pandas (optional)

## Overview

Add support for structured data formats (CSV and Excel) where each row is processed as a separate document. The system will:
1. Read CSV/XLSX files row-by-row
2. Convert each row to a dictionary (column name → value)
3. Allow selective field redaction via preprocessor
4. Merge redacted values back into the original dictionary
5. Write results back to CSV/XLSX format

## Architecture

### Data Flow

```
CSV/XLSX File
    ↓
Reader (csv_file or xlsx_file)
    ↓ yields: {"col1": "value1", "col2": "value2", ...}
Preprocessor (field_selector)
    ↓ yields: {"content": "col1_value col2_value", "metadata": {"original": {...}, "selected_fields": [...]}}
Redactor
    ↓ yields: {"content": "<PERSON:hash> <EMAIL:hash>", ...}
Postprocessor (dict_merger)
    ↓ yields: {"col1": "<PERSON:hash>", "col2": "<EMAIL:hash>", "col3": "unchanged", ...}
Writer (csv_file or xlsx_file)
    ↓
Redacted CSV/XLSX File
```

---

## 1. CSV Reader

### Component: `CSVReader`

**File**: `src/scruby/readers/csv_file.py`

**Registration**: `@reader_registry.register_decorator("csv_file")`

### Functionality

- Read CSV files with configurable delimiter, quoting, encoding
- Treat first row as headers (column names)
- Each subsequent row becomes a dictionary
- Handle missing values (empty strings)
- Support for different encodings (UTF-8, Latin-1, etc.)

### Configuration

```yaml
readers:
  csv_file:
    delimiter: ","
    quotechar: '"'
    encoding: "utf-8"
    skip_empty_rows: true
```

### Output Format

Each row yields:
```python
{
    "content": None,  # Will be populated by preprocessor
    "metadata": {
        "source": "file.csv",
        "row_number": 2,
        "original_data": {
            "Name": "John Smith",
            "Email": "john@example.com",
            "Phone": "555-1234",
            "Notes": "Patient history..."
        }
    }
}
```

### Example

```python
from scruby.readers import CSVReader

reader = CSVReader("patients.csv")
for document in reader.read():
    print(document["metadata"]["original_data"])
    # {"Name": "John", "Email": "john@example.com", ...}
```

---

## 2. XLSX Reader

### Component: `XLSXReader`

**File**: `src/scruby/readers/xlsx_file.py`

**Registration**: `@reader_registry.register_decorator("xlsx_file")`

**Dependencies**: `openpyxl`

### Functionality

- Read Excel (.xlsx) files
- Support multiple sheets (default: first sheet)
- First row as headers
- Each subsequent row becomes a dictionary
- Handle different cell types (string, number, date, formula)
- Convert dates to ISO format strings
- Handle merged cells gracefully

### Configuration

```yaml
readers:
  xlsx_file:
    sheet_name: 0  # 0 for first sheet, or "Sheet1" for named sheet
    encoding: "utf-8"
    skip_empty_rows: true
    date_format: "%Y-%m-%d"
```

### Output Format

Same as CSV Reader:
```python
{
    "content": None,
    "metadata": {
        "source": "file.xlsx",
        "sheet": "Sheet1",
        "row_number": 2,
        "original_data": {
            "Name": "John Smith",
            "DOB": "1980-05-15",
            "SSN": "123-45-6789"
        }
    }
}
```

### Example

```python
from scruby.readers import XLSXReader

reader = XLSXReader("patients.xlsx", sheet_name="Patient Data")
for document in reader.read():
    print(document["metadata"]["original_data"])
```

---

## 3. Field Selector Preprocessor

### Component: `FieldSelectorPreprocessor`

**File**: `src/scruby/preprocessors/field_selector.py`

**Registration**: `@preprocessor_registry.register_decorator("field_selector")`

### Functionality

- Select specific fields from the original data dictionary for redaction
- Concatenate selected fields into `content` string
- Preserve original dictionary in metadata
- Support field name patterns (wildcards, regex)
- Support exclusion patterns

### Configuration

```yaml
preprocessors:
  field_selector:
    # Exact field names to redact
    fields:
      - "Name"
      - "Email"
      - "SSN"
      - "Notes"
    # Separator between fields when concatenating
    separator: " | "
    # Keep field structure for targeted redaction
    preserve_field_mapping: true
```

### Behavior

**Input:**
```python
{
    "metadata": {
        "original_data": {
            "ID": "12345",
            "Name": "John Smith",
            "Email": "john@example.com",
            "Phone": "555-1234",
            "Notes": "Patient has SSN 123-45-6789"
        }
    }
}
```

**Output:**
```python
{
    "content": "John Smith | john@example.com | 555-1234 | Patient has SSN 123-45-6789",
    "metadata": {
        "original_data": {
            "ID": "12345",
            "Name": "John Smith",
            "Email": "john@example.com",
            "Phone": "555-1234",
            "Notes": "Patient has SSN 123-45-6789"
        },
        "selected_fields": ["Name", "Email", "Phone", "Notes"],
        "field_boundaries": [
            {"field": "Name", "start": 0, "end": 10},
            {"field": "Email", "start": 13, "end": 31},
            {"field": "Phone", "start": 34, "end": 42},
            {"field": "Notes", "start": 45, "end": 77}
        ]
    }
}
```

### Alternative: Field-by-Field Processing

For more precise control, process each field independently:

**Configuration:**
```yaml
preprocessors:
  field_selector:
    mode: "independent"  # vs "concatenate" (default)
    fields: ["Name", "Email", "Notes"]
```

**Behavior**: Preprocessor yields multiple documents (one per field), each redacted independently.

---

## 4. Dictionary Merger Postprocessor

### Component: `DictMergerPostprocessor`

**File**: `src/scruby/postprocessors/dict_merger.py`

**Registration**: `@postprocessor_registry.register_decorator("dict_merger")`

### Functionality

- Takes redacted `content` string
- Maps redacted entities back to their original fields
- Merges with original dictionary
- Preserves non-redacted fields unchanged
- Handles field boundaries correctly

### Configuration

```yaml
postprocessors:
  dict_merger:
    # Keep original values for non-selected fields
    preserve_unselected: true
    # Add metadata about redaction
    add_redaction_metadata: false
```

### Behavior

**Input:**
```python
{
    "content": "<PERSON:abc123> | <EMAIL_ADDRESS:def456> | <PHONE_NUMBER:ghi789> | Patient has <US_SSN:jkl012>",
    "metadata": {
        "original_data": {
            "ID": "12345",
            "Name": "John Smith",
            "Email": "john@example.com",
            "Phone": "555-1234",
            "Notes": "Patient has SSN 123-45-6789"
        },
        "selected_fields": ["Name", "Email", "Phone", "Notes"],
        "field_boundaries": [
            {"field": "Name", "start": 0, "end": 10},
            {"field": "Email", "start": 13, "end": 31},
            {"field": "Phone", "start": 34, "end": 42},
            {"field": "Notes", "start": 45, "end": 77}
        ]
    }
}
```

**Output:**
```python
{
    "content": None,  # Cleared
    "metadata": {
        "original_data": {...},
        "redacted_data": {
            "ID": "12345",  # Unchanged
            "Name": "<PERSON:abc123>",
            "Email": "<EMAIL_ADDRESS:def456>",
            "Phone": "<PHONE_NUMBER:ghi789>",
            "Notes": "Patient has <US_SSN:jkl012>"
        }
    }
}
```

---

## 5. CSV Writer

### Component: `CSVWriter`

**File**: `src/scruby/writers/csv_file.py`

**Registration**: `@writer_registry.register_decorator("csv_file")`

### Functionality

- Write dictionary data to CSV format
- Extract data from `metadata["redacted_data"]`
- Preserve column order from original file
- Write headers on first row
- Handle missing values
- Support different encodings and delimiters

### Configuration

```yaml
writers:
  csv_file:
    delimiter: ","
    quotechar: '"'
    encoding: "utf-8"
    write_header: true
```

### Example

```python
from scruby.writers import CSVWriter

writer = CSVWriter("redacted_patients.csv")
writer.write(document)  # Writes row with redacted data
```

---

## 6. XLSX Writer

### Component: `XLSXWriter`

**File**: `src/scruby/writers/xlsx_file.py`

**Registration**: `@writer_registry.register_decorator("xlsx_file")`

**Dependencies**: `openpyxl`

### Functionality

- Write dictionary data to Excel format
- Create new workbook or append to existing sheet
- Preserve formatting (optional)
- Write headers on first row
- Support multiple sheets
- Handle different data types

### Configuration

```yaml
writers:
  xlsx_file:
    sheet_name: "Redacted Data"
    write_header: true
    preserve_formatting: false  # May be complex
```

---

## Dependencies

Add to `pyproject.toml`:

```toml
[project]
dependencies = [
    # ... existing dependencies ...
    "openpyxl>=3.1.0",  # For XLSX support
]

[project.optional-dependencies]
csv = []  # Built-in csv module
xlsx = ["openpyxl>=3.1.0"]
structured = ["openpyxl>=3.1.0", "pandas>=2.0.0"]  # Optional: pandas for advanced features
```

---

## Configuration Example

### config.yaml

```yaml
# Structured data support
readers:
  csv_file:
    delimiter: ","
    encoding: "utf-8"
  
  xlsx_file:
    sheet_name: 0  # First sheet
    skip_empty_rows: true

preprocessors:
  field_selector:
    fields:
      - "Name"
      - "Email" 
      - "SSN"
      - "PatientNotes"
    separator: " | "

postprocessors:
  dict_merger:
    preserve_unselected: true

writers:
  csv_file:
    delimiter: ","
    encoding: "utf-8"
  
  xlsx_file:
    sheet_name: "Redacted"
```

---

## CLI Usage

### CSV File

```bash
# Redact CSV with field selection
scruby \
  --reader csv_file \
  --src patients.csv \
  --out redacted_patients.csv \
  --writer csv_file \
  --preprocessors field_selector \
  --postprocessors dict_merger \
  --verbose
```

### XLSX File

```bash
# Redact Excel file
scruby \
  --reader xlsx_file \
  --src patients.xlsx \
  --out redacted_patients.xlsx \
  --writer xlsx_file \
  --preprocessors field_selector \
  --postprocessors dict_merger \
  --verbose
```

### With Custom Config

```bash
scruby \
  --src patients.xlsx \
  --out redacted_patients.xlsx \
  --config structured_config.yaml \
  --verbose
```

---

## Testing Strategy

### Unit Tests

**File**: `tests/test_structured_readers.py`

```python
def test_csv_reader_basic()
def test_csv_reader_with_special_chars()
def test_csv_reader_encoding()
def test_xlsx_reader_basic()
def test_xlsx_reader_multiple_sheets()
def test_xlsx_reader_date_handling()
```

**File**: `tests/test_field_selector.py`

```python
def test_field_selector_basic()
def test_field_selector_with_patterns()
def test_field_selector_preserve_boundaries()
def test_field_selector_empty_fields()
```

**File**: `tests/test_dict_merger.py`

```python
def test_dict_merger_basic()
def test_dict_merger_preserve_unselected()
def test_dict_merger_with_boundaries()
def test_dict_merger_complex_redactions()
```

**File**: `tests/test_structured_writers.py`

```python
def test_csv_writer_basic()
def test_csv_writer_preserves_order()
def test_xlsx_writer_basic()
def test_xlsx_writer_multiple_sheets()
```

### Integration Tests

**File**: `tests/test_structured_integration.py`

```python
def test_csv_end_to_end_redaction()
def test_xlsx_end_to_end_redaction()
def test_field_selection_preserves_structure()
def test_hash_consistency_across_rows()
```

### Test Data

**File**: `tests/data/test_patients.csv`

```csv
ID,Name,Email,SSN,Notes
1,John Smith,john@example.com,123-45-6789,Regular checkup
2,Jane Doe,jane@example.com,987-65-4321,Follow-up appointment
```

**File**: `tests/data/test_patients.xlsx`

Same data in Excel format with proper headers and data types.

---

## Implementation Order

1. **Phase 1: Readers** (2-3 hours)
   - [ ] Implement `CSVReader`
   - [ ] Implement `XLSXReader`
   - [ ] Unit tests for readers
   - [ ] Add openpyxl dependency

2. **Phase 2: Field Selector** (1-2 hours)
   - [ ] Implement `FieldSelectorPreprocessor`
   - [ ] Add field boundary tracking
   - [ ] Unit tests

3. **Phase 3: Dict Merger** (1-2 hours)
   - [ ] Implement `DictMergerPostprocessor`
   - [ ] Handle field mapping
   - [ ] Unit tests

4. **Phase 4: Writers** (2-3 hours)
   - [ ] Implement `CSVWriter`
   - [ ] Implement `XLSXWriter`
   - [ ] Unit tests

5. **Phase 5: Integration** (1-2 hours)
   - [ ] End-to-end tests
   - [ ] Test with real dataset (mendeley_testing_dataset.xlsx)
   - [ ] Update documentation

**Total Estimated Time**: 7-12 hours

---

## Edge Cases to Handle

1. **Empty Fields**: Handle empty/null values in CSV/XLSX
2. **Special Characters**: Quotes, commas, newlines in CSV
3. **Data Types**: Numbers, dates, booleans in Excel
4. **Large Files**: Memory-efficient processing (streaming)
5. **Column Order**: Preserve original column order in output
6. **Missing Headers**: Handle files without headers
7. **Duplicate Column Names**: Handle or error gracefully
8. **Field Boundaries**: Correctly map redacted text back to fields

---

## Future Enhancements

1. **Pandas Integration**: Optional pandas backend for better performance
2. **Multi-sheet Support**: Process multiple sheets in one XLSX file
3. **Column Mapping**: Rename columns during processing
4. **Data Validation**: Validate data types before/after redaction
5. **Incremental Processing**: Process large files in chunks
6. **Format Preservation**: Preserve Excel formatting (colors, fonts, etc.)
7. **Formula Handling**: Handle Excel formulas appropriately

---

## Success Criteria

- ✅ Can read CSV and XLSX files row-by-row
- ✅ Each row processed as separate document
- ✅ Field selector works with configurable field lists
- ✅ Dict merger correctly maps redacted content back to fields
- ✅ Output CSV/XLSX preserves structure and column order
- ✅ Hash consistency maintained across rows (same PII = same hash)
- ✅ Non-selected fields remain unchanged
- ✅ >90% test coverage
- ✅ Works with mendeley_testing_dataset.xlsx

---

## Questions for Clarification

1. **Field Selection**: Should field selection be in config file or CLI parameter?
2. **Multiple Sheets**: Should we process all sheets or just one?
3. **Output Format**: Same format as input, or allow CSV→XLSX conversion?
4. **Large Files**: Should we implement streaming/chunking from the start?
5. **Pandas**: Should we use pandas as optional dependency for better performance?

---

## References

- **CSV Format**: [Python csv module](https://docs.python.org/3/library/csv.html)
- **XLSX Format**: [openpyxl documentation](https://openpyxl.readthedocs.io/)
- **Reader Pattern**: [specs/03-reader-components.md](03-reader-components.md)
- **Preprocessor Pattern**: [specs/05-preprocessor-components.md](05-preprocessor-components.md)
- **Postprocessor Pattern**: [specs/08-postprocessor-components.md](08-postprocessor-components.md)
