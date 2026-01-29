# Scruby Usage Guide

This guide provides practical examples of using the `scruby` CLI tool to redact PII from text files.

## Table of Contents

- [Quick Start](#quick-start)
- [Basic Examples](#basic-examples)
- [Advanced Usage](#advanced-usage)
- [Options Reference](#options-reference)
- [Common Scenarios](#common-scenarios)
- [Understanding Output](#understanding-output)

---

## Quick Start

### Simplest Usage - Output to stdout

```bash
scruby --src myfile.txt
```

**Example:**
```bash
$ cat tests/data/simple_patient.txt
Patient: John Smith
SSN: 123-45-6789
Email: john@example.com

$ scruby --src tests/data/simple_patient.txt
Patient: <PERSON:94a49cd76fbc>
<ORGANIZATION:19581a105154>: <US_SSN:5b93cb60b097>
Email: <EMAIL_ADDRESS:446133b1ab2c>
```

---

## Basic Examples

### 1. Redact to a File

```bash
scruby --src input.txt --out output.txt
```

**Example:**
```bash
$ scruby --src tests/data/simple_patient.txt --out /tmp/redacted.txt
$ cat /tmp/redacted.txt
Patient: <PERSON:94a49cd76fbc>
<ORGANIZATION:19581a105154>: <US_SSN:5b93cb60b097>
Email: <EMAIL_ADDRESS:446133b1ab2c>
```

### 2. Redact with Verbose Output

```bash
scruby --src input.txt --out output.txt --verbose
```

**Example:**
```bash
$ scruby --src tests/data/simple_patient.txt --out /tmp/redacted.txt --verbose
Processing: tests/data/simple_patient.txt
Output: /tmp/redacted.txt
Reader: text_file
Writer: text_file

Processed 1 document(s)
Redacted 4 PII entities
```

### 3. Redact a Directory

```bash
scruby --src input_folder/ --out output_folder/
```

**Note**: Add trailing slashes to indicate directories. The tool will:
- Process all `.txt` files in the input folder
- Create corresponding redacted files in the output folder
- Preserve filenames

**Example:**
```bash
$ scruby --src tests/data/multi_dir/ --out /tmp/redacted_dir/ --verbose
Processing directory: tests/data/multi_dir/
Output directory: /tmp/redacted_dir/

Processed 2 document(s)
Redacted 12 PII entities
```

---

## Advanced Usage

### 4. Using Preprocessors

Preprocessors clean and normalize text before redaction.

```bash
scruby --src input.txt --preprocessors whitespace_normalizer
```

**Available Preprocessors:**
- `whitespace_normalizer` - Normalizes whitespace, tabs, line breaks
- `text_cleaner` - Removes control characters, normalizes quotes

**Example:**
```bash
$ scruby --src tests/data/whitespace_test.txt \
  --preprocessors whitespace_normalizer \
  --verbose

Processing with preprocessors: whitespace_normalizer
Processed 1 document(s)
```

### 5. Using Postprocessors

Postprocessors clean up the redacted output.

```bash
scruby --src input.txt --postprocessors redaction_cleaner
```

**Available Postprocessors:**
- `redaction_cleaner` - Merges consecutive redactions, cleans spacing
- `format_preserver` - Maintains document formatting

**Example:**
```bash
$ scruby --src input.txt \
  --postprocessors redaction_cleaner,format_preserver
```

### 6. Adjusting Confidence Threshold

Control how strict entity detection should be (0.0 to 1.0).

```bash
scruby --src input.txt --threshold 0.8
```

- **Lower threshold (e.g., 0.3)**: More sensitive, may have false positives
- **Higher threshold (e.g., 0.9)**: More strict, may miss some PII
- **Default**: 0.6 (balanced)

**Example:**
```bash
$ scruby --src input.txt --threshold 0.3 --verbose
Using confidence threshold: 0.3
Redacted 15 PII entities

$ scruby --src input.txt --threshold 0.9 --verbose
Using confidence threshold: 0.9
Redacted 8 PII entities
```

### 7. Using Custom Configuration

```bash
scruby --src input.txt --config my_config.yaml
```

**Example custom config (`custom_config.yaml`):**
```yaml
hmac_secret: "my-secret-key"
default_confidence_threshold: 0.7
redaction_strategy: "hash"

presidio:
  spacy_model: "en_core_web_lg"
  entities:
    - PERSON
    - EMAIL_ADDRESS
    - PHONE_NUMBER
    - US_SSN
    - MEDICAL_RECORD_NUMBER
```

**Usage:**
```bash
$ scruby --src input.txt --config custom_config.yaml --verbose
Using configuration: custom_config.yaml
Using confidence threshold: 0.7
```

---

## Options Reference

### Required Options

| Option | Description | Example |
|--------|-------------|---------|
| `--src`, `-s` | Input file or directory | `--src input.txt` |

### Optional Options

| Option | Short | Description | Default | Example |
|--------|-------|-------------|---------|---------|
| `--out`, `-o` | `-o` | Output file  or directory | stdout | `--out output.txt` |
| `--verbose`, `-v` | `-v` | Show detailed progress | False | `--verbose` |
| `--config` | | Path to config file | `config.yaml` | `--config custom.yaml` |
| `--threshold` | | Confidence threshold (0.0-1.0) | 0.6 | `--threshold 0.8` |
| `--preprocessors` | | Comma-separated preprocessors | None | `--preprocessors whitespace_normalizer` |
| `--postprocessors` | | Comma-separated postprocessors | None | `--postprocessors redaction_cleaner` |
| `--reader` | | Reader type | `text_file` | `--reader text_file` |
| `--writer` | | Writer type (auto-detected) | auto | `--writer stdout` |
| `--version` | | Show version | | `--version` |
| `--help` | | Show help message | | `--help` |

---

## Common Scenarios

### Scenario 1: Redact Medical Records

```bash
# Single patient record
scruby --src patient_record.txt \
  --out redacted_patient.txt \
  --postprocessors redaction_cleaner \
  --verbose

# Batch process multiple records
scruby --src patient_records/ \
  --out redacted_records/ \
  --postprocessors redaction_cleaner \
  --verbose
```

### Scenario 2: Quick Preview (Stdout)

```bash
# Preview redaction without saving
scruby --src sensitive_doc.txt | head -20

# Pipe to another tool
scruby --src docs/ | grep "<PERSON:" | wc -l
```

### Scenario 3: Strict Redaction for Compliance

```bash
# Use high threshold and clean output
scruby --src compliance_doc.txt \
  --out redacted_doc.txt \
  --threshold 0.4 \
  --preprocessors whitespace_normalizer,text_cleaner \
  --postprocessors redaction_cleaner \
  --verbose
```

### Scenario 4: Testing with Different Thresholds

```bash
# Test with low threshold
scruby --src test.txt --threshold 0.3 --verbose | tee output_low.txt

# Test with high threshold  
scruby --src test.txt --threshold 0.9 --verbose | tee output_high.txt

# Compare results
diff output_low.txt output_high.txt
```

---

## Understanding Output

### Redaction Format

Redacted entities use the format: `<ENTITY_TYPE:hash>`

**Examples:**
```
<PERSON:94a49cd76fbc>         # Person's name
<US_SSN:5b93cb60b097>         # Social Security Number
<EMAIL_ADDRESS:446133b1ab2c>  # Email address
<PHONE_NUMBER:18e83743e0e7>   # Phone number
<DATE_TIME:ba60cd6a09ca>      # Date/time
<ORGANIZATION:19581a105154>   # Organization name
<MEDICAL_RECORD_NUMBER:20807a093da4>  # MRN
```

### Hash Consistency

**Important**: The same PII value always produces the same hash (within the same HMAC key).

**Example:**
```text
# Input
Patient 1: John Smith, SSN: 123-45-6789
Patient 2: Jane Doe, SSN: 123-45-6789

# Output
Patient 1: <PERSON:94a49cd76fbc>, SSN: <US_SSN:5b93cb60b097>
Patient 2: <PERSON:a1b2c3d4e5f6>, SSN: <US_SSN:5b93cb60b097>
```

Note: Both patients have the same SSN, so they get the same hash `5b93cb60b097`.

### Entity Types Detected

Scruby detects all 18 HIPAA PII identifiers:

1. **PERSON** - Names
2. **LOCATION** - Cities, addresses (< state level)
3. **DATE_TIME** - Dates (except year)
4. **PHONE_NUMBER** - Phone/fax numbers
5. **EMAIL_ADDRESS** - Email addresses
6. **US_SSN** - Social Security Numbers
7. **MEDICAL_RECORD_NUMBER** - MRN (custom)
8. **PRESCRIPTION_NUMBER** - RX numbers (custom)
9. **INSURANCE_ID** - Insurance IDs (custom)
10. **CREDIT_CARD** - Credit card numbers
11. **URL** - Web addresses
12. **IP_ADDRESS** - IP addresses
13. **US_DRIVER_LICENSE** - Driver's license
14. **US_PASSPORT** - Passport numbers
15. **ORGANIZATION** - Company/org names
16. And more...

---

##Troubleshooting

### No Output

**Problem**: Command runs but produces no output

**Solution**:
```bash
# Check if file exists
ls -l input.txt

# Use verbose mode to see what's happening
scruby --src input.txt --verbose
```

### Too Much Redaction

**Problem**: Too many entities are being redacted

**Solution**:
```bash
# Increase threshold to be more strict
scruby --src input.txt --threshold 0.8
```

### Too Little Redaction

**Problem**: Some PII is not being redacted

**Solution**:
```bash
# Decrease threshold to be more sensitive
scruby --src input.txt --threshold 0.3

# Check if entity type is supported
scruby --help
```

### Permission Errors

**Problem**: Cannot write to output file

**Solution**:
```bash
# Check output directory permissions
ls -ld /path/to/output/

# Use a different output location
scruby --src input.txt --out ~/redacted.txt
```

---

## Tips & Best Practices

### 1. Always Test First

Preview output before writing to files:
```bash
scruby --src input.txt | head -50
```

### 2. Use Verbose Mode for Production

Track what's being processed:
```bash
scruby --src data/ --out redacted/ --verbose 2>&1 | tee redaction.log
```

### 3. Consistent HMAC Keys

Use the same `hmac_secret` in `config.yaml` to maintain hash consistency across runs.

### 4. Backup Original Files

Always keep originals before batch processing:
```bash
cp -r original_data/ backup/
scruby --src original_data/ --out redacted_data/ --verbose
```

### 5. Combine Processors for Best Results

```bash
scruby --src messy_input.txt \
  --preprocessors whitespace_normalizer,text_cleaner \
  --postprocessors redaction_cleaner \
  --out clean_redacted.txt
```

---

## Next Steps

- Review [README.md](README.md) for installation and architecture
- See [config.yaml](config.yaml) for configuration options
- Check [specs/](specs/) for detailed technical documentation
- Run tests: `pytest -v`

---

## Getting Help

```bash
# Show help message
scruby --help

# Show version
scruby --version

# Report issues
# Visit: https://github.com/yourusername/scruby/issues
```
