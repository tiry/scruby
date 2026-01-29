# Scruby

A Python CLI tool to process and redact HIPAA PII (Personally Identifiable Information) from text data.

## Overview

Scruby uses Microsoft Presidio for entity detection and anonymization, providing a pluggable pipeline architecture for processing text documents and redacting all 18 HIPAA PII identifiers.

## Features

- **HIPAA Compliance**: Detects and redacts all 18 HIPAA PII identifiers
- **Pluggable Architecture**: Easy to extend with custom readers, writers, preprocessors, and postprocessors
- **HMAC-based Hashing**: Consistent anonymization using keyed hashes
- **Flexible Configuration**: YAML-based configuration with sensible defaults
- **spaCy Integration**: Uses spaCy's en_core_web_lg model for accurate entity detection

## Project Status

**Current Status**: Step 1 Complete - Project Setup & Configuration

### Completed
- ✅ Project structure (src/ layout)
- ✅ Python virtual environment setup
- ✅ Configuration management with YAML
- ✅ Comprehensive unit tests (91% coverage)

### In Progress
- 🔄 Registry & factory pattern implementation
- 🔄 Pipeline components (readers, writers, preprocessors, postprocessors)
- 🔄 Presidio integration with custom recognizers
- 🔄 CLI implementation

## Installation

### Prerequisites

- Python 3.11 or higher
- pip

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd scruby
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install the package in development mode:
```bash
pip install -e ".[dev]"
```

4. Download the spaCy language model (will be required for full functionality):
```bash
python -m spacy download en_core_web_lg
```

## Configuration

Scruby uses a YAML configuration file (default: `config.yaml`) to manage settings:

```yaml
hmac_secret: "your-secret-key"
default_confidence_threshold: 0.5

processing:
  max_files: -1
  verbose: false

presidio:
  language: "en"
  spacy_model: "en_core_web_lg"
  entities:
    - PERSON
    - LOCATION
    - DATE_TIME
    - PHONE_NUMBER
    - EMAIL_ADDRESS
    - US_SSN
    - MEDICAL_RECORD_NUMBER
    - HEALTH_PLAN_ID
    - ACCOUNT_NUMBER
    - LICENSE_NUMBER
    - VIN
    - DEVICE_ID
    - URL
    - IP_ADDRESS
    - CRYPTO
```

## Development

### Running Tests

Run all tests:
```bash
pytest
```

Run tests with coverage:
```bash
pytest --cov=src/scruby --cov-report=html
```

Run specific test file:
```bash
pytest tests/test_config.py -v
```

### Project Structure

```
scruby/
├── src/
│   └── scruby/
│       ├── __init__.py
│       └── config.py           # Configuration management
├── tests/
│   ├── __init__.py
│   ├── test_config.py          # Configuration tests
│   └── fixtures/               # Test fixtures
├── specs/                      # Detailed specifications
├── pyproject.toml              # Project metadata and dependencies
├── config.yaml                 # Default configuration
└── README.md                   # This file
```

## 18 HIPAA PII Identifiers

Scruby detects and redacts all 18 HIPAA identifiers as defined by the HIPAA Privacy Rule:

1. Names (patient, family members, employers)
2. Geographic subdivisions smaller than state
3. Dates (except year)
4. Telephone numbers
5. Fax numbers
6. Email addresses
7. Social Security numbers
8. Medical record numbers (MRN)
9. Health plan beneficiary numbers
10. Account numbers
11. Certificate/license numbers
12. Vehicle identifiers (VINs)
13. Device identifiers and serial numbers
14. URLs
15. IP addresses
16. Biometric identifiers
17. Full-face photos and comparable images
18. Any other unique identifying characteristics

## Architecture

Scruby uses a pluggable pipeline architecture with five main components:

1. **READ**: Read documents from source
2. **PRE-PROCESS**: Extract fields to redact
3. **REDACT**: Detect and redact PII entities
4. **POST-PROCESS**: Merge redacted fields back
5. **SAVE**: Write processed documents to destination

Each component is pluggable via abstract base classes, registries, and factories.

## License

MIT

## Contributing

See `specs/00-implementation-plan.md` for the detailed implementation plan and current progress.
