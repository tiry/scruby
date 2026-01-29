"""Tests for configuration management."""

import pytest
from pathlib import Path

from scruby.config import (
    Config,
    ConfigurationError,
    ProcessingConfig,
    PresidioConfig,
    load_config,
    get_default_config,
)


class TestLoadConfig:
    """Tests for loading configuration from files."""

    def test_load_valid_config(self):
        """Load a valid config file and verify all fields."""
        config_path = Path(__file__).parent / "fixtures" / "test_config.yaml"
        config = load_config(config_path)

        assert config.hmac_secret == "test-secret-key"
        assert config.default_confidence_threshold == 0.7
        assert config.processing.max_files == 10
        assert config.processing.verbose is True
        assert config.presidio.language == "en"
        assert config.presidio.spacy_model == "en_core_web_lg"
        assert config.presidio.entities == ["PERSON", "EMAIL_ADDRESS", "PHONE_NUMBER"]

    def test_load_config_with_defaults(self):
        """Load config with missing optional fields, verify defaults are applied."""
        # Create a minimal config file
        import tempfile
        import yaml

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(
                {
                    "hmac_secret": "test-secret",
                    # default_confidence_threshold missing - should default to 0.5
                    # processing section missing - should use defaults
                    # presidio section missing - should use defaults
                },
                f,
            )
            temp_path = f.name

        try:
            config = load_config(temp_path)
            assert config.hmac_secret == "test-secret"
            assert config.default_confidence_threshold == 0.5
            assert config.processing.max_files == -1
            assert config.processing.verbose is False
            assert config.presidio.language == "en"
            assert config.presidio.spacy_model == "en_core_web_lg"
            assert config.presidio.entities == []
        finally:
            Path(temp_path).unlink()

    def test_load_missing_config_file(self):
        """Attempt to load non-existent file, verify error is raised."""
        with pytest.raises(ConfigurationError) as exc_info:
            load_config("nonexistent.yaml")

        assert "Configuration file not found" in str(exc_info.value)

    def test_load_invalid_yaml(self):
        """Load file with invalid YAML syntax, verify error is raised."""
        import tempfile

        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False
        ) as f:
            f.write("invalid: yaml: syntax: [[[")
            temp_path = f.name

        try:
            with pytest.raises(ConfigurationError) as exc_info:
                load_config(temp_path)

            assert "Invalid YAML" in str(exc_info.value)
        finally:
            Path(temp_path).unlink()

    def test_config_custom_path(self):
        """Load config from custom path with both Path and str."""
        config_path = Path(__file__).parent / "fixtures" / "test_config.yaml"

        # Test with Path object
        config1 = load_config(config_path)
        assert config1.hmac_secret == "test-secret-key"

        # Test with string
        config2 = load_config(str(config_path))
        assert config2.hmac_secret == "test-secret-key"

    def test_config_relative_path(self):
        """Load config using relative path."""
        config_path = Path(__file__).parent / "fixtures" / "test_config.yaml"
        config = load_config(config_path)
        assert config.hmac_secret == "test-secret-key"


class TestConfigValidation:
    """Tests for configuration validation."""

    def test_validate_hmac_secret_empty(self):
        """Create config with empty hmac_secret, verify validation fails."""
        config = Config(
            hmac_secret="",
            default_confidence_threshold=0.5,
            processing=ProcessingConfig(max_files=-1, verbose=False),
            presidio=PresidioConfig(language="en", spacy_model="en_core_web_lg", entities=[]),
        )

        with pytest.raises(ConfigurationError) as exc_info:
            config.validate()

        assert "hmac_secret cannot be empty" in str(exc_info.value)

    def test_validate_confidence_threshold_too_low(self):
        """Test confidence threshold < 0.0, verify validation fails."""
        config = Config(
            hmac_secret="test",
            default_confidence_threshold=-0.1,
            processing=ProcessingConfig(max_files=-1, verbose=False),
            presidio=PresidioConfig(language="en", spacy_model="en_core_web_lg", entities=[]),
        )

        with pytest.raises(ConfigurationError) as exc_info:
            config.validate()

        assert "default_confidence_threshold must be between 0.0 and 1.0" in str(
            exc_info.value
        )

    def test_validate_confidence_threshold_too_high(self):
        """Test confidence threshold > 1.0, verify validation fails."""
        config = Config(
            hmac_secret="test",
            default_confidence_threshold=1.5,
            processing=ProcessingConfig(max_files=-1, verbose=False),
            presidio=PresidioConfig(language="en", spacy_model="en_core_web_lg", entities=[]),
        )

        with pytest.raises(ConfigurationError) as exc_info:
            config.validate()

        assert "default_confidence_threshold must be between 0.0 and 1.0" in str(
            exc_info.value
        )

    def test_validate_confidence_threshold_bounds_valid(self):
        """Test confidence threshold at valid boundaries (0.0 and 1.0)."""
        config1 = Config(
            hmac_secret="test",
            default_confidence_threshold=0.0,
            processing=ProcessingConfig(max_files=-1, verbose=False),
            presidio=PresidioConfig(language="en", spacy_model="en_core_web_lg", entities=[]),
        )
        config1.validate()  # Should not raise

        config2 = Config(
            hmac_secret="test",
            default_confidence_threshold=1.0,
            processing=ProcessingConfig(max_files=-1, verbose=False),
            presidio=PresidioConfig(language="en", spacy_model="en_core_web_lg", entities=[]),
        )
        config2.validate()  # Should not raise

    def test_validate_max_files_invalid(self):
        """Test max_files < -1, verify validation fails."""
        config = Config(
            hmac_secret="test",
            default_confidence_threshold=0.5,
            processing=ProcessingConfig(max_files=-2, verbose=False),
            presidio=PresidioConfig(language="en", spacy_model="en_core_web_lg", entities=[]),
        )

        with pytest.raises(ConfigurationError) as exc_info:
            config.validate()

        assert "processing.max_files must be -1 or positive" in str(exc_info.value)

    def test_validate_max_files_valid(self):
        """Test max_files with valid values (-1, 0, positive)."""
        # Test -1 (unlimited)
        config1 = Config(
            hmac_secret="test",
            default_confidence_threshold=0.5,
            processing=ProcessingConfig(max_files=-1, verbose=False),
            presidio=PresidioConfig(language="en", spacy_model="en_core_web_lg", entities=[]),
        )
        config1.validate()  # Should not raise

        # Test 0
        config2 = Config(
            hmac_secret="test",
            default_confidence_threshold=0.5,
            processing=ProcessingConfig(max_files=0, verbose=False),
            presidio=PresidioConfig(language="en", spacy_model="en_core_web_lg", entities=[]),
        )
        config2.validate()  # Should not raise

        # Test positive
        config3 = Config(
            hmac_secret="test",
            default_confidence_threshold=0.5,
            processing=ProcessingConfig(max_files=100, verbose=False),
            presidio=PresidioConfig(language="en", spacy_model="en_core_web_lg", entities=[]),
        )
        config3.validate()  # Should not raise

    def test_load_invalid_config_file(self):
        """Load invalid config file and verify proper validation."""
        config_path = Path(__file__).parent / "fixtures" / "invalid_config.yaml"

        with pytest.raises(ConfigurationError) as exc_info:
            load_config(config_path)

        # Should catch one of the validation errors
        error_msg = str(exc_info.value)
        assert (
            "hmac_secret cannot be empty" in error_msg
            or "default_confidence_threshold must be between" in error_msg
            or "processing.max_files must be" in error_msg
        )


class TestDefaultConfig:
    """Tests for default configuration."""

    def test_get_default_config(self):
        """Get default config and verify structure is valid."""
        config = get_default_config()

        assert isinstance(config, Config)
        assert config.hmac_secret == "default-secret-key-change-in-production"
        assert config.default_confidence_threshold == 0.5
        assert config.processing.max_files == -1
        assert config.processing.verbose is False
        assert config.presidio.language == "en"
        assert config.presidio.spacy_model == "en_core_web_lg"
        assert len(config.presidio.entities) == 15  # All 15 HIPAA entity types

    def test_default_config_validates(self):
        """Verify default config passes validation."""
        config = get_default_config()
        config.validate()  # Should not raise

    def test_default_config_has_all_hipaa_entities(self):
        """Verify default config includes all required HIPAA identifiers."""
        config = get_default_config()

        expected_entities = [
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
        ]

        for entity in expected_entities:
            assert entity in config.presidio.entities
