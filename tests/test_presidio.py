"""Tests for Presidio integration."""

import pytest

from scruby.presidio import (
    InsuranceIDRecognizer,
    MRNRecognizer,
    PresidioAnalyzer,
    PrescriptionNumberRecognizer,
    RecognizerRegistry,
    get_recognizer_registry,
)


class TestCustomRecognizers:
    """Tests for custom HIPAA recognizers."""

    def test_mrn_recognizer_initialization(self):
        """Verify MRN recognizer initializes correctly."""
        recognizer = MRNRecognizer()
        assert recognizer.supported_entities == ["MEDICAL_RECORD_NUMBER"]
        assert len(recognizer.patterns) == 2

    def test_prescription_recognizer_initialization(self):
        """Verify prescription recognizer initializes correctly."""
        recognizer = PrescriptionNumberRecognizer()
        assert recognizer.supported_entities == ["PRESCRIPTION_NUMBER"]
        assert len(recognizer.patterns) == 2

    def test_insurance_recognizer_initialization(self):
        """Verify insurance ID recognizer initializes correctly."""
        recognizer = InsuranceIDRecognizer()
        assert recognizer.supported_entities == ["INSURANCE_ID"]
        assert len(recognizer.patterns) == 2


class TestRecognizerRegistry:
    """Tests for the recognizer registry."""

    def test_registry_defaults(self):
        """Verify default recognizers are registered."""
        registry = RecognizerRegistry()
        recognizers = registry.get_all_recognizers()
        
        assert len(recognizers) == 3
        entity_types = [r.supported_entities[0] for r in recognizers]
        assert "MEDICAL_RECORD_NUMBER" in entity_types
        assert "PRESCRIPTION_NUMBER" in entity_types
        assert "INSURANCE_ID" in entity_types

    def test_add_custom_recognizer(self):
        """Add new recognizer to registry."""
        registry = RecognizerRegistry()
        initial_count = len(registry.get_all_recognizers())
        
        new_recognizer = MRNRecognizer()
        registry.add_recognizer(new_recognizer)
        
        assert len(registry.get_all_recognizers()) == initial_count + 1

    def test_get_all_recognizers(self):
        """Retrieve all registered recognizers."""
        registry = RecognizerRegistry()
        recognizers = registry.get_all_recognizers()
        
        assert isinstance(recognizers, list)
        assert len(recognizers) > 0

    def test_registry_clear(self):
        """Clear registry."""
        registry = RecognizerRegistry()
        registry.clear()
        
        assert len(registry.get_all_recognizers()) == 0

    def test_singleton_registry(self):
        """Verify get_recognizer_registry returns singleton."""
        registry1 = get_recognizer_registry()
        registry2 = get_recognizer_registry()
        
        assert registry1 is registry2


@pytest.mark.slow
class TestPresidioAnalyzer:
    """Tests for Presidio analyzer wrapper."""

    def test_analyzer_initialization(self):
        """Verify analyzer initializes correctly."""
        analyzer = PresidioAnalyzer()
        
        assert analyzer.language == "en"
        assert analyzer.analyzer is not None
        assert analyzer.config is not None

    def test_get_supported_entities(self):
        """List all supported entity types."""
        analyzer = PresidioAnalyzer()
        entities = analyzer.get_supported_entities()
        
        assert isinstance(entities, list)
        assert len(entities) > 0
        # Check for some built-in entities
        assert "PERSON" in entities or "EMAIL_ADDRESS" in entities
        # Check for custom entities
        assert "MEDICAL_RECORD_NUMBER" in entities
        assert "PRESCRIPTION_NUMBER" in entities
        assert "INSURANCE_ID" in entities

    def test_analyze_with_builtin_entities(self):
        """Detect built-in entities."""
        analyzer = PresidioAnalyzer()
        text = "John Doe's email is john.doe@example.com"
        
        results = analyzer.analyze(text, entities=["PERSON", "EMAIL_ADDRESS"])
        
        # Should detect at least one entity
        assert len(results) > 0
        entity_types = [r.entity_type for r in results]
        assert "PERSON" in entity_types or "EMAIL_ADDRESS" in entity_types

    def test_analyze_mrn(self):
        """Detect medical record numbers."""
        analyzer = PresidioAnalyzer()
        text = "Patient MRN 12345678 was admitted today."
        
        results = analyzer.analyze(text, entities=["MEDICAL_RECORD_NUMBER"])
        
        # Should detect MRN
        assert len(results) > 0
        assert results[0].entity_type == "MEDICAL_RECORD_NUMBER"

    def test_analyze_prescription(self):
        """Detect prescription numbers."""
        analyzer = PresidioAnalyzer()
        text = "Prescription #1234567 for medication."
        
        results = analyzer.analyze(text, entities=["PRESCRIPTION_NUMBER"])
        
        # Should detect prescription number
        assert len(results) > 0
        assert results[0].entity_type == "PRESCRIPTION_NUMBER"

    def test_analyze_with_confidence_threshold(self):
        """Respect confidence threshold setting."""
        # Create analyzer with high confidence threshold
        config = {"presidio_confidence_threshold": 0.9}
        analyzer = PresidioAnalyzer(config=config)
        
        text = "Maybe John Smith"
        results = analyzer.analyze(text, entities=["PERSON"])
        
        # High threshold may filter out low-confidence results
        # This test just verifies no errors occur
        assert isinstance(results, list)

    def test_analyze_uses_config_entities(self):
        """Use entities from configuration."""
        config = {
            "entities_to_redact": ["PERSON", "EMAIL_ADDRESS"],
            "presidio_confidence_threshold": 0.5
        }
        analyzer = PresidioAnalyzer(config=config)
        
        text = "Contact john.doe@example.com for info."
        # Don't specify entities - should use from config
        results = analyzer.analyze(text)
        
        assert isinstance(results, list)
