"""Presidio analyzer wrapper."""

from typing import Any, Dict, List, Optional

from presidio_analyzer import AnalyzerEngine, RecognizerResult
from presidio_analyzer.nlp_engine import NlpEngineProvider

from scruby.config import load_config

from .recognizer_registry import get_recognizer_registry


class PresidioAnalyzer:
    """
    Wrapper around Presidio AnalyzerEngine with custom configuration.
    
    Integrates custom recognizers and configuration from config.yaml.
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        language: str = "en"
    ):
        """
        Initialize Presidio analyzer.
        
        Args:
            config: Configuration dictionary (loads from file if None)
            language: Language for NLP processing
        """
        self.config = config or load_config()
        self.language = language
        
        # Create NLP engine provider
        nlp_config = {
            "nlp_engine_name": "spacy",
            "models": [{"lang_code": language, "model_name": "en_core_web_lg"}]
        }
        provider = NlpEngineProvider(nlp_configuration=nlp_config)
        nlp_engine = provider.create_engine()
        
        # Create analyzer with custom recognizers
        self.analyzer = AnalyzerEngine(nlp_engine=nlp_engine)
        
        # Register custom recognizers
        self._register_custom_recognizers()
    
    def _register_custom_recognizers(self) -> None:
        """Register custom recognizers from the registry."""
        registry = get_recognizer_registry()
        for recognizer in registry.get_all_recognizers():
            self.analyzer.registry.add_recognizer(recognizer)
    
    def analyze(
        self,
        text: str,
        entities: Optional[List[str]] = None,
        language: Optional[str] = None
    ) -> List[RecognizerResult]:
        """
        Analyze text for PII entities.
        
        Args:
            text: Text to analyze
            entities: List of entity types to detect (uses config if None)
            language: Language override
            
        Returns:
            List of RecognizerResult objects
        """
        # Use configured entities if not specified
        if entities is None:
            if isinstance(self.config, dict):
                entities = self.config.get("entities_to_redact", [])
            else:
                entities = getattr(self.config, "entities_to_redact", [])
        
        # Get confidence threshold from config
        if isinstance(self.config, dict):
            score_threshold = self.config.get("presidio_confidence_threshold", 0.5)
        else:
            score_threshold = getattr(self.config, "presidio_confidence_threshold", 0.5)
        
        # Analyze text
        results = self.analyzer.analyze(
            text=text,
            entities=entities,
            language=language or self.language,
            score_threshold=score_threshold
        )
        
        return results
    
    def get_supported_entities(self) -> List[str]:
        """Get list of all supported entity types."""
        return self.analyzer.get_supported_entities(language=self.language)


class PresidioAnalyzerError(Exception):
    """Raised when Presidio analyzer encounters an error."""
    pass
