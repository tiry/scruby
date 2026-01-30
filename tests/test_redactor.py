"""Tests for the redactor component."""

import pytest

from scruby.redactor import Redactor, RedactorError


class TestRedactorInitialization:
    """Tests for redactor initialization."""

    def test_redactor_initialization(self):
        """Verify redactor initializes correctly."""
        redactor = Redactor()
        
        assert redactor.config is not None
        assert redactor.analyzer is not None
        assert redactor.anonymizer is not None

    def test_redactor_with_config(self):
        """Initialize with custom configuration."""
        config = {"redaction_strategy": "mask"}
        redactor = Redactor(config=config)
        
        assert redactor.config == config


@pytest.mark.slow
class TestRedactionStrategies:
    """Tests for different redaction strategies."""

    def test_redact_with_replace_strategy(self):
        """Replace entities with [REDACTED]."""
        redactor = Redactor()
        document = {
            "content": "Email: john.doe@example.com",
            "metadata": {"source": "test"}
        }
        
        result = redactor.redact(document, entities=["EMAIL_ADDRESS"], strategy="replace")
        
        assert "[REDACTED]" in result["content"]
        assert "john.doe@example.com" not in result["content"]
        assert result["metadata"]["redaction_strategy"] == "replace"
        assert result["metadata"]["source"] == "test"

    def test_redact_with_mask_strategy(self):
        """Mask entities with asterisks."""
        redactor = Redactor()
        document = {"content": "Email: test@example.com"}
        
        result = redactor.redact(document, entities=["EMAIL_ADDRESS"], strategy="mask")
        
        assert "*" in result["content"]
        assert "test@example.com" not in result["content"]
        assert result["metadata"]["redaction_strategy"] == "mask"

    def test_redact_with_hash_strategy(self):
        """Hash entities with detailed verification."""
        redactor = Redactor()
        document = {"content": "Contact john.doe@example.com"}
        
        result = redactor.redact(document, entities=["EMAIL_ADDRESS"], strategy="hash")
        
        # Verify original email is gone
        assert "john.doe@example.com" not in result["content"]
        # Verify hash format is present (e.g., <EMAIL_ADDRESS:abc123>)
        assert "<EMAIL_ADDRESS:" in result["content"]
        assert ">" in result["content"]
        # Verify metadata
        assert result["metadata"]["redaction_strategy"] == "hash"
        assert result["metadata"]["redacted_entities"] >= 1

    def test_redact_builtin_entities(self):
        """Redact built-in entity types with verification."""
        redactor = Redactor()
        document = {"content": "Contact John Doe at john.doe@example.com"}
        
        result = redactor.redact(document, entities=["PERSON", "EMAIL_ADDRESS"])
        
        # Should redact at least one entity
        assert result["metadata"]["redacted_entities"] > 0
        # Verify content was actually modified
        assert result["content"] != document["content"]
        # Check that sensitive info is removed
        assert "john.doe@example.com" not in result["content"]

    def test_redact_custom_entities(self):
        """Redact custom HIPAA entities."""
        redactor = Redactor()
        document = {"content": "Patient MRN 12345678 prescribed RX 9876543"}
        
        result = redactor.redact(
            document,
            entities=["MEDICAL_RECORD_NUMBER", "PRESCRIPTION_NUMBER"]
        )
        
        assert "MRN 12345678" not in result["content"]
        assert "RX 9876543" not in result["content"]
        assert result["metadata"]["redacted_entities"] == 2


class TestMetadata:
    """Tests for metadata handling."""

    def test_metadata_preserved(self):
        """Original metadata is preserved."""
        redactor = Redactor()
        document = {
            "content": "Test content",
            "metadata": {"source": "test.txt", "author": "John"}
        }
        
        result = redactor.redact(document, entities=[])
        
        assert result["metadata"]["source"] == "test.txt"
        assert result["metadata"]["author"] == "John"

    def test_metadata_enriched(self):
        """Adds redaction info to metadata."""
        redactor = Redactor()
        document = {"content": "Email: test@example.com"}
        
        result = redactor.redact(document, entities=["EMAIL_ADDRESS"], strategy="replace")
        
        assert "redacted_entities" in result["metadata"]
        assert "redaction_strategy" in result["metadata"]
        assert result["metadata"]["redaction_strategy"] == "replace"

    def test_redacted_entities_count(self):
        """Counts redacted entities correctly."""
        redactor = Redactor()
        document = {"content": "test@example.com and another@example.com"}
        
        result = redactor.redact(document, entities=["EMAIL_ADDRESS"])
        
        assert result["metadata"]["redacted_entities"] == 2


class TestErrorHandling:
    """Tests for error handling."""

    def test_missing_content_key(self):
        """Handle document without content key."""
        redactor = Redactor()
        document = {"metadata": {"source": "test"}}
        
        with pytest.raises(RedactorError, match="must contain 'content' key"):
            redactor.redact(document)

    def test_invalid_strategy(self):
        """Handle unknown redaction strategy."""
        redactor = Redactor()
        document = {"content": "test"}
        
        with pytest.raises(RedactorError, match="Unknown redaction strategy"):
            redactor.redact(document, strategy="invalid_strategy")

    def test_redact_empty_document(self):
        """Handle empty content."""
        redactor = Redactor()
        document = {"content": ""}
        
        result = redactor.redact(document)
        
        assert result["content"] == ""
        assert result["metadata"]["redacted_entities"] == 0
