# Test Data for Scruby

This folder contains test data files used for testing the scruby PII redaction tool.

## Test Files Overview

### Core Test Files

| File | Purpose | Contents |
|------|---------|----------|
| `patient_record.txt` | Comprehensive medical record testing | Full patient demographics, insurance, medical details, and multiple PHI identifiers |
| `employee_info.txt` | Workplace/HR context testing | Names, emails, phone numbers, SSN |
| `repeated_entities.txt` | Hash normalization testing | Same entity in different cases and whitespace patterns |

### Integration Test Files

| File | Purpose | Used In |
|------|---------|---------|
| `simple_patient.txt` | Basic pipeline testing | `test_complete_pipeline_with_hash_strategy()` |
| `whitespace_test.txt` | Preprocessor/postprocessor testing | `test_pipeline_with_preprocessors_and_postprocessors()`, `test_cli_with_all_options()` |
| `cli_test.txt` | CLI integration testing | `test_cli_end_to_end()` |
| `medical_record.txt` | Real-world scenario testing | `test_medical_record_redaction()` |

### Test Directories

| Directory | Purpose | Contents |
|-----------|---------|----------|
| `multi_dir/` | Batch processing testing | `file1.txt` (Alice Brown), `file2.txt` (Bob Johnson) |

## File Details

### patient_record.txt
Complete medical record with HIPAA identifiers:
- Patient name, DOB, SSN, MRN
- Contact: address, phone, email
- Insurance: Health Plan ID, Account Number
- Medical: prescription numbers, device IDs
- Additional: VIN, IP address, URLs, license numbers

### employee_info.txt
Employee information:
- Employee names
- Contact information
- Social Security Numbers

### repeated_entities.txt
Hash normalization test data:
- "John Michael Smith" (proper case)
- "john michael smith" (lowercase)
- "john    Michael  smith" (irregular whitespace)

All variations should produce the same hash after normalization.

### simple_patient.txt
Basic patient data:
```
Patient: John Smith
SSN: 123-45-6789
Email: john@example.com
```

### whitespace_test.txt
Irregular whitespace and casing:
```
Name:    John    Smith
Email: JOHN@EXAMPLE.COM
```

### cli_test.txt
Simple CLI test data:
```
Patient: Sarah Williams
DOB: January 1, 1990
```

### medical_record.txt
Complete medical record for integration testing:
- Patient: Jane Elizabeth Doe
- Full demographics and insurance
- 8+ PHI identifiers for comprehensive testing

### multi_dir/
Directory with multiple files:
- **file1.txt**: Patient Alice Brown with SSN
- **file2.txt**: Patient Bob Johnson with phone number

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
scruby --src tests/data/whitespace_test.txt \
  --out redacted.txt \
  --preprocessors whitespace_normalizer
```

### With Postprocessors

```bash
scruby --src tests/data/patient_record.txt \
  --out redacted.txt \
  --postprocessors redaction_cleaner
```

### Complete Pipeline

```bash
scruby --src tests/data/medical_record.txt \
  --out redacted.txt \
  --preprocessors whitespace_normalizer \
  --postprocessors redaction_cleaner \
  --verbose
```

### Override Confidence Threshold

```bash
scruby --src tests/data/patient_record.txt \
  --threshold 0.8 \
  --verbose
```

### Process Multiple Files (Directory)

```bash
scruby --src tests/data/multi_dir/ --out output/ --verbose
```

## Expected PII Types

The test files contain various PHI identifiers that should be redacted:

- **Names**: John Michael Smith, Jane Elizabeth Doe, Alice Brown, Bob Johnson
- **Dates**: January 15, 1985, March 15, 1985, January 1, 1990
- **SSN**: 123-45-6789, 987-65-4321, 111-22-3333
- **Phone Numbers**: (617) 555-0123, (555) 987-6543, (555) 123-4567
- **Email Addresses**: john@example.com, john.smith@email.com, jane.doe@email.com
- **Addresses**: 456 Oak Street, Boston, MA 02108, 123 Main Street, Boston, MA 02108
- **URLs**: https://patient-portal.hospital.com/john-smith
- **IP Addresses**: 192.168.1.100
- **Medical Record Numbers**: MRN-2024-789456, MRN-2024-123456
- **Health Plan IDs**: HP-987654321, HP-111222333
- **Account Numbers**: ACC-2024-556677, ACC-2024-987654
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
