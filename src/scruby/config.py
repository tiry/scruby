"""Configuration management for scruby."""

from dataclasses import dataclass
from pathlib import Path
from typing import List

import yaml


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
    redaction_strategy: str
    processing: ProcessingConfig
    presidio: PresidioConfig
    _raw_config: dict = None  # Store the full raw config for dict-like access

    def get(self, key: str, default=None):
        """Dict-like get method to access raw config values."""
        if self._raw_config:
            return self._raw_config.get(key, default)
        return default

    def validate(self) -> None:
        """
        Validate configuration values.

        Raises:
            ConfigurationError: If configuration is invalid
        """
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
    path = Path(config_path)

    if not path.exists():
        raise ConfigurationError(f"Configuration file not found: {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML in configuration file: {e}") from e
    except Exception as e:
        raise ConfigurationError(f"Failed to read configuration file: {e}") from e

    if not isinstance(data, dict):
        raise ConfigurationError("Configuration file must contain a YAML dictionary")

    try:
        # Extract processing config with defaults
        processing_data = data.get("processing", {})
        processing = ProcessingConfig(
            max_files=processing_data.get("max_files", -1),
            verbose=processing_data.get("verbose", False),
        )

        # Extract presidio config with defaults
        presidio_data = data.get("presidio", {})
        presidio = PresidioConfig(
            language=presidio_data.get("language", "en"),
            spacy_model=presidio_data.get("spacy_model", "en_core_web_lg"),
            entities=presidio_data.get("entities", []),
        )

        # Create main config
        config = Config(
            hmac_secret=data.get("hmac_secret", ""),
            default_confidence_threshold=data.get("default_confidence_threshold", 0.5),
            redaction_strategy=data.get("redaction_strategy", "hash"),
            processing=processing,
            presidio=presidio,
            _raw_config=data,  # Store full raw config for dict-like access
        )

        # Validate configuration
        config.validate()

        return config

    except KeyError as e:
        raise ConfigurationError(f"Missing required configuration key: {e}") from e
    except TypeError as e:
        raise ConfigurationError(f"Invalid configuration value type: {e}") from e


def get_default_config() -> Config:
    """
    Get default configuration.

    Returns:
        Config instance with default values
    """
    return Config(
        hmac_secret="default-secret-key-change-in-production",
        default_confidence_threshold=0.5,
        redaction_strategy="hash",
        processing=ProcessingConfig(max_files=-1, verbose=False),
        presidio=PresidioConfig(
            language="en",
            spacy_model="en_core_web_lg",
            entities=[
                "PERSON",
                "LOCATION",
                "DATE_TIME",
                "PHONE_NUMBER",
                "EMAIL_ADDRESS",
                "US_SSN",
                "MEDICAL_RECORD_NUMBER",
                "HEALTH_PLAN_ID",
                "ACCOUNT_NUMBER",
                "LICENSE_NUMBER",
                "VIN",
                "DEVICE_ID",
                "URL",
                "IP_ADDRESS",
                "CRYPTO",
            ],
        ),
    )
