"""Document redactor using Presidio."""

import hashlib
import hmac
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
            
            # Use custom hash implementation for "hash" strategy
            if strategy == "hash":
                redacted_text = self._custom_hash_redaction(text, results)
            else:
                # Build operators for other strategies
                operators = self._build_operators(strategy)
                
                # Anonymize text
                anonymized = self.anonymizer.anonymize(
                    text=text,
                    analyzer_results=results,
                    operators=operators
                )
                redacted_text = anonymized.text
            
            # Return redacted document
            return {
                **document,
                "content": redacted_text,
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
            # Use hash with entity type prefix format
            operator = OperatorConfig("hash", {"hash_type": "sha256"})
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
    
    def _custom_hash_redaction(self, text: str, results: List[Any]) -> str:
        """
        Perform custom hash-based redaction with entity type prefix.
        
        Args:
            text: Original text
            results: Analyzer results with entity locations
            
        Returns:
            Text with entities replaced by <ENTITY_TYPE:hash>
        """
        # Get HMAC secret
        secret = self._get_encryption_key()
        
        # Sort results by start position in reverse order to avoid offset issues
        sorted_results = sorted(results, key=lambda x: x.start, reverse=True)
        
        # Replace each entity with hashed version
        redacted = text
        for result in sorted_results:
            entity_text = text[result.start:result.end]
            entity_type = result.entity_type
            
            # Create HMAC-SHA1 hash (shorter than SHA256)
            hash_digest = hmac.new(
                secret.encode('utf-8'),
                entity_text.encode('utf-8'),
                hashlib.sha1
            ).hexdigest()
            
            # Use first 12 characters for readability (still secure with HMAC)
            short_digest = hash_digest[:12]
            
            # Format: <ENTITY_TYPE:hash>
            replacement = f"<{entity_type}:{short_digest}>"
            
            # Replace in text
            redacted = redacted[:result.start] + replacement + redacted[result.end:]
        
        return redacted


class RedactorError(Exception):
    """Raised when redaction fails."""
    pass
