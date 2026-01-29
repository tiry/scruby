# Test Data for Scruby CLI

This folder contains sample files with PII data for testing the scruby CLI tool.

## Test Files

1. **patient_record.txt** - Sample medical record with various HIPAA identifiers
2. **employee_info.txt** - Employee information with personal data

## CLI Usage Examples

### Basic Usage - Output to stdout

```bash
scruby --src tests/data/patient_record.txt
```

### Save to File

```bash
scruby --src tests/data/patient_record.txt --out tests/data/patient_record_redacted.txt
```

### Verbose Mode

```bash
scruby --src tests/data/patient_record.txt --out tests/data/patient_record_redacted.txt --verbose
```

### With Preprocessors

```bash
scruby --src tests/data/employee_info.txt \
  --out tests/data/employee_info_redacted.txt \
  --preprocessors whitespace_normalizer
```

### With Postprocessors

```bash
scruby --src tests/data/patient_record.txt \
  --out tests/data/patient_record_redacted.txt \
  --postprocessors redaction_cleaner
```

### Complete Pipeline

```bash
scruby --src tests/data/patient_record.txt \
  --out tests/data/patient_record_redacted.txt \
  --preprocessors whitespace_normalizer,text_cleaner \
  --postprocessors redaction_cleaner,format_preserver \
  --verbose
```

### Override Confidence Threshold

```bash
scruby --src tests/data/patient_record.txt \
  --threshold 0.8 \
  --verbose
```

### Process Multiple Files (Directory)

First create a directory with multiple .txt files, then:

```bash
mkdir -p tests/data/input tests/data/output

# Copy test files to input directory
cp tests/data/patient_record.txt tests/data/input/
cp tests/data/employee_info.txt tests/data/input/

# Process entire directory
scruby --src tests/data/input/ --out tests/data/output/ --verbose
```

## Expected PII Types

The test files contain the following types of PII that should be redacted:

- **Names**: John Michael Smith, Sarah Johnson, Michael Johnson
- **Dates**: January 15, 1985, March 20, 2024, February 1, 2020
- **SSN**: 123-45-6789, 987-65-4321
- **Phone Numbers**: (617) 555-0123, (555) 123-4567, (555) 987-6543
- **Email Addresses**: john.smith@email.com, sarah.johnson@company.com
- **Addresses**: 456 Oak Street, Boston, MA 02108, 123 Elm Street, Springfield, IL 62701
- **URLs**: https://patient-portal.hospital.com/john-smith, vpn.company.com
- **IP Addresses**: 192.168.1.100, 10.0.1.50
- **Medical Record Numbers**: MRN-2024-789456
- **Health Plan IDs**: HP-987654321, HI-123456789
- **Account Numbers**: ACC-2024-556677
- **License Numbers**: DL-MA-S12345678
- **VINs**: 1HGBH41JXMN109186
- **Device IDs**: DEV-SN-998877
- **Prescription Numbers**: RX-2024-445566

## Installation

Make sure you're in the scruby directory and have activated the virtual environment:

```bash
cd /Users/thierry.delprat/dev/scruby
source venv/bin/activate
```

The scruby CLI should be available through the entry point configured in pyproject.toml.
