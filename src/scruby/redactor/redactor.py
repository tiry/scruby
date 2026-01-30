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
    
    def _get_config_value(self, key: str, default=None):
        """
        Get configuration value with support for both dict and Config object.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        if isinstance(self.config, dict):
            return self.config.get(key, default)
        else:
            return getattr(self.config, key, default)
    
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
            
            # Resolve overlapping entities
            results = self._resolve_conflicts(results)
            
            # Get redaction strategy
            if strategy is None:
                strategy = self._get_config_value("redaction_strategy", "replace")
            
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
        return self._get_config_value("hmac_secret", "default-key-change-me")
    
    def _resolve_conflicts(self, results: List[Any]) -> List[Any]:
        """
        Resolve overlapping entity detections.
        
        When entities overlap, prioritize:
        1. Higher confidence scores
        2. More specific entity types (e.g., US_SSN > ORGANIZATION)
        3. Longer spans
        
        Args:
            results: List of RecognizerResult objects
            
        Returns:
            Filtered list without overlapping entities
        """
        if not results:
            return results
        
        # Define entity type priorities (higher number = higher priority)
        ENTITY_PRIORITIES = {
            'US_SSN': 100,
            'EMAIL_ADDRESS': 95,
            'PHONE_NUMBER': 90,
            'CREDIT_CARD': 85,
            'MEDICAL_RECORD_NUMBER': 80,
            'PRESCRIPTION_NUMBER': 75,
            'INSURANCE_ID': 70,
            'PERSON': 60,
            'DATE_TIME': 50,
            'LOCATION': 40,
            'ORGANIZATION': 30,  # Lower priority for generic types
            'DEFAULT': 10
        }
        
        def get_priority(result):
            """Get priority score for an entity."""
            entity_priority = ENTITY_PRIORITIES.get(result.entity_type, ENTITY_PRIORITIES['DEFAULT'])
            confidence = result.score
            span_length = result.end - result.start
            # Combine factors: priority (most important), confidence, length
            return (entity_priority, confidence, span_length)
        
        def overlaps(r1, r2):
            """Check if two results overlap."""
            return not (r1.end <= r2.start or r2.end <= r1.start)
        
        # Sort by start position
        sorted_results = sorted(results, key=lambda x: x.start)
        
        # Filter overlapping entities
        filtered = []
        for current in sorted_results:
            # Check if current overlaps with any already filtered result
            should_add = True
            to_remove = []
            
            for i, existing in enumerate(filtered):
                if overlaps(current, existing):
                    # Compare priorities
                    if get_priority(current) > get_priority(existing):
                        # Current has higher priority, remove existing
                        to_remove.append(i)
                    else:
                        # Existing has higher/equal priority, skip current
                        should_add = False
                        break
            
            # Remove lower priority conflicts
            for i in reversed(to_remove):
                filtered.pop(i)
            
            # Add current if it wins all conflicts
            if should_add:
               filtered.append(current)
        
        return filtered
    
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
            
            # Normalize entity text for consistent hashing
            # - Convert to lowercase
            # - Normalize whitespace (collapse multiple spaces to single, trim)
            import re
            normalized_text = re.sub(r'\s+', ' ', entity_text.lower().strip())
            
            # Create HMAC-SHA1 hash (shorter than SHA256)
            hash_digest = hmac.new(
                secret.encode('utf-8'),
                normalized_text.encode('utf-8'),
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
