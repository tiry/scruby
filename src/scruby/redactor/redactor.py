"""Document redactor using Presidio."""

from typing import Any, Dict, List, Optional

from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

from scruby.config import load_config
from scruby.presidio import PresidioAnalyzer


class Redactor:
    """
    Redacts PII from documents using Presidio.
    
    Combines PresidioAnalyzer for detection with AnonymizerEngine
    for redaction.
    """
    
    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        analyzer: Optional[PresidioAnalyzer] = None
    ):
        """
        Initialize the redactor.
        
        Args:
            config: Configuration dictionary (loads from file if None)
            analyzer: Pre-configured PresidioAnalyzer (creates new if None)
        """
        self.config = config or load_config()
        self.analyzer = analyzer or PresidioAnalyzer(config=self.config)
        self.anonymizer = AnonymizerEngine()
    
    def redact(
        self,
        document: Dict[str, Any],
        entities: Optional[List[str]] = None,
        strategy: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Redact PII from a document.
        
        Args:
            document: Document with 'content' and optional 'metadata'
            entities: Entity types to redact (uses config if None)
            strategy: Redaction strategy (uses config if None)
            
        Returns:
            Redacted document with modified content
            
        Raises:
            RedactorError: If redaction fails
        """
        if "content" not in document:
            raise RedactorError("Document must contain 'content' key")
        
        try:
            text = document["content"]
            
            # Analyze text for PII
            results = self.analyzer.analyze(text, entities=entities)
            
            # Get redaction strategy
            if strategy is None:
                if isinstance(self.config, dict):
                    strategy = self.config.get("redaction_strategy", "replace")
                else:
                    strategy = getattr(self.config, "redaction_strategy", "replace")
            
            # Build operators for anonymization
            operators = self._build_operators(strategy)
            
            # Anonymize text
            anonymized = self.anonymizer.anonymize(
                text=text,
                analyzer_results=results,
                operators=operators
            )
            
            # Return redacted document
            return {
                **document,
                "content": anonymized.text,
                "metadata": {
                    **document.get("metadata", {}),
                    "redacted_entities": len(results),
                    "redaction_strategy": strategy
                }
            }
        except RedactorError:
            raise
        except Exception as e:
            raise RedactorError(f"Failed to redact document: {e}") from e
    
    def _build_operators(self, strategy: str) -> Dict[str, OperatorConfig]:
        """
        Build operator configuration for anonymization.
        
        Args:
            strategy: Redaction strategy name
            
        Returns:
            Dictionary mapping entity types to operators
        """
        # Map strategy names to Presidio operators
        if strategy == "replace":
            operator = OperatorConfig("replace", {"new_value": "[REDACTED]"})
        elif strategy == "mask":
            operator = OperatorConfig("mask", {"masking_char": "*", "chars_to_mask": 100, "from_end": False})
        elif strategy == "hash":
            operator = OperatorConfig("hash")
        elif strategy == "encrypt":
            operator = OperatorConfig("encrypt", {"key": self._get_encryption_key()})
        else:
            raise RedactorError(f"Unknown redaction strategy: {strategy}")
        
        # Apply strategy to all entity types
        return {"DEFAULT": operator}
    
    def _get_encryption_key(self) -> str:
        """Get encryption key from config."""
        if isinstance(self.config, dict):
            key = self.config.get("hmac_secret", "default-key-change-me")
        else:
            key = getattr(self.config, "hmac_secret", "default-key-change-me")
        return key


class RedactorError(Exception):
    """Raised when redaction fails."""
    pass
