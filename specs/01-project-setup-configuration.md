# Step 1: Project Setup & Configuration

**Status**: ✅ Complete  
**Related Spec**: `specs/00-implementation-plan.md`

---

## Goals

1. Set up Python virtual environment (venv)
2. Create project directory structure (src/ layout)
3. Define `pyproject.toml` with all dependencies
4. Implement configuration loading module (`config.py`)
5. Create default `config.yaml` file
6. Implement comprehensive unit tests

---

## Project Structure

```
scruby/
├── .gitignore
├── pyproject.toml              # Project metadata and dependencies
├── config.yaml                 # Default configuration
├── README.md                   # Basic project documentation
├── venv/                       # Python virtual environment (excluded from git)
├── src/
│   └── scruby/
│       ├── __init__.py
│       └── config.py           # Configuration loading module
└── tests/
    ├── __init__.py
    ├── test_config.py          # Configuration tests
    └── fixtures/
        ├── test_config.yaml    # Test configuration file
        └── invalid_config.yaml # Invalid config for error testing
```

---

## Dependencies

### Core Dependencies
- **click** (^8.1.7) - CLI framework
- **presidio-analyzer** (^2.2.0) - PII detection
- **presidio-anonymizer** (^2.2.0) - PII anonymization
- **spacy** (^3.7.0) - NLP library
- **pyyaml** (^6.0.1) - YAML configuration parsing

### Development Dependencies
- **pytest** (^8.0.0) - Testing framework
- **pytest-cov** (^4.1.0) - Code coverage
- **pytest-mock** (^3.12.0) - Mocking support

### Post-install
- **en_core_web_lg** - spaCy large English model (installed via spaCy CLI)

---

## Configuration Schema

### config.yaml Structure

```yaml
# HMAC secret key for entity hashing
# WARNING: Keep this secret! Change in production!
hmac_secret: "default-secret-key-change-in-production"

# Minimum confidence score for entity detection (0.0 to 1.0)
# Lower values detect more entities but may have false positives
default_confidence_threshold: 0.5

# Processing options
processing:
  # Maximum number of files to process (-1 = unlimited)
  max_files: -1
  
  # Enable verbose logging
  verbose: false

# Presidio configuration
presidio:
  # Language for NLP model
  language: "en"
  
  # spaCy model to use
  spacy_model: "en_core_web_lg"
  
  # Supported entity types (all 18 HIPAA identifiers)
  entities:
    - PERSON                    # Names
    - LOCATION                  # Geographic subdivisions
    - DATE_TIME                 # Dates
    - PHONE_NUMBER              # Phone numbers
    - EMAIL_ADDRESS             # Email addresses
    - US_SSN                    # Social Security numbers
    - MEDICAL_RECORD_NUMBER     # MRN (custom)
    - HEALTH_PLAN_ID            # Health plan numbers (custom)
    - ACCOUNT_NUMBER            # Account numbers
    - LICENSE_NUMBER            # Certificate/License numbers (custom)
    - VIN                       # Vehicle identifiers (custom)
    - DEVICE_ID                 # Device identifiers
    - URL                       # URLs
    - IP_ADDRESS                # IP addresses
    - CRYPTO                    # Biometric/unique identifiers
```

---

## Implementation Details

### config.py Module

The configuration module will provide:

1. **Configuration Class** (`Config`)
   - Dataclass or Pydantic model to hold configuration
   - Type hints for all fields
   - Validation logic

2. **Configuration Loader** (`load_config()`)
   - Load YAML file from specified path
   - Apply defaults for missing values
   - Validate configuration schema
   - Return `Config` instance

3. **Error Handling**
   - `ConfigurationError` custom exception
   - Clear error messages for:
     - Missing config file
     - Invalid YAML syntax
     - Missing required fields
     - Invalid field values

### API Design

```python
from typing import List, Optional
from dataclasses import dataclass
from pathlib import Path

class ConfigurationError(Exception):
    """Raised when configuration is invalid or cannot be loaded."""
    pass

@dataclass
class PresidioConfig:
    """Presidio-specific configuration."""
    language: str
    spacy_model: str
    entities: List[str]

@dataclass
class ProcessingConfig:
    """Processing options."""
    max_files: int
    verbose: bool

@dataclass
class Config:
    """Main configuration class."""
    hmac_secret: str
    default_confidence_threshold: float
    processing: ProcessingConfig
    presidio: PresidioConfig
    
    def validate(self) -> None:
        """Validate configuration values."""
        if not self.hmac_secret:
            raise ConfigurationError("hmac_secret cannot be empty")
        
        if not 0.0 <= self.default_confidence_threshold <= 1.0:
            raise ConfigurationError(
                f"default_confidence_threshold must be between 0.0 and 1.0, "
                f"got {self.default_confidence_threshold}"
            )
        
        if self.processing.max_files < -1:
            raise ConfigurationError(
                f"processing.max_files must be -1 or positive, "
                f"got {self.processing.max_files}"
            )

def load_config(config_path: str | Path = "config.yaml") -> Config:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Config instance
        
    Raises:
        ConfigurationError: If config cannot be loaded or is invalid
    """
    pass  # Implementation to be added

def get_default_config() -> Config:
    """
    Get default configuration.
    
    Returns:
        Config instance with default values
    """
    pass  # Implementation to be added
```

---

## Unit Tests

### Test Coverage (`tests/test_config.py`)

1. **test_load_valid_config**
   - Load a valid config file
   - Verify all fields are correctly parsed
   - Verify types are correct

2. **test_load_config_with_defaults**
   - Load config with some missing optional fields
   - Verify defaults are applied

3. **test_load_missing_config_file**
   - Attempt to load non-existent file
   - Verify `ConfigurationError` is raised
   - Verify error message is clear

4. **test_load_invalid_yaml**
   - Load file with invalid YAML syntax
   - Verify `ConfigurationError` is raised

5. **test_validate_hmac_secret_empty**
   - Create config with empty hmac_secret
   - Verify validation fails

6. **test_validate_confidence_threshold_bounds**
   - Test confidence threshold < 0.0
   - Test confidence threshold > 1.0
   - Verify validation fails for both

7. **test_validate_max_files_invalid**
   - Test max_files < -1
   - Verify validation fails

8. **test_get_default_config**
   - Get default config
   - Verify structure is valid
   - Verify sensible defaults

9. **test_config_custom_path**
   - Load config from custom path
   - Verify it works with Path and str

10. **test_config_relative_path**
    - Load config using relative path
    - Verify resolution works correctly

### Test Fixtures

**fixtures/test_config.yaml**:
```yaml
hmac_secret: "test-secret-key"
default_confidence_threshold: 0.7
processing:
  max_files: 10
  verbose: true
presidio:
  language: "en"
  spacy_model: "en_core_web_lg"
  entities:
    - PERSON
    - EMAIL_ADDRESS
```

**fixtures/invalid_config.yaml**:
```yaml
hmac_secret: ""  # Invalid - empty
default_confidence_threshold: 1.5  # Invalid - out of range
```

---

## pyproject.toml

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "scruby"
version = "0.1.0"
description = "A Python CLI tool to process and redact HIPAA PII from text data"
authors = [
    {name = "Scruby Contributors"}
]
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
keywords = ["redaction", "pii", "hipaa", "privacy", "cli"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Intended Audience :: Healthcare Industry",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Topic :: Security",
    "Topic :: Text Processing",
]

dependencies = [
    "click>=8.1.7",
    "presidio-analyzer>=2.2.0",
    "presidio-anonymizer>=2.2.0",
    "spacy>=3.7.0",
    "pyyaml>=6.0.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.12.0",
]

[project.scripts]
scruby = "scruby.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--verbose",
    "--cov=src/scruby",
    "--cov-report=term-missing",
    "--cov-report=html",
]

[tool.coverage.run]
source = ["src/scruby"]
omit = ["*/tests/*", "*/test_*.py"]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
    "if TYPE_CHECKING:",
]
```

---

## .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python

# Virtual environment
venv/
env/
ENV/

# Testing
.pytest_cache/
.coverage
htmlcov/
*.cover

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Build
build/
dist/
*.egg-info/

# Config (if containing secrets)
config.local.yaml
```

---

## Installation & Setup Steps

1. **Create virtual environment**:
   ```bash
   python3.11 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -e ".[dev]"
   ```

3. **Download spaCy model**:
   ```bash
   python -m spacy download en_core_web_lg
   ```

4. **Verify installation**:
   ```bash
   pytest tests/test_config.py
   ```

---

## Success Criteria

- ✅ Virtual environment created and activated
- ✅ Project structure matches specification
- ✅ All dependencies install without errors
- ✅ spaCy en_core_web_lg model downloaded
- ✅ `config.py` module implemented with proper type hints
- ✅ Configuration loading works correctly
- ✅ Configuration validation catches all invalid cases
- ✅ All unit tests pass
- ✅ Test coverage >90% for `config.py`
- ✅ Error messages are clear and helpful

---

## Next Step

After completing Step 1, proceed to:
**Step 2: Registry & Factory Pattern** (`specs/02-registry-factory-pattern.md`)
