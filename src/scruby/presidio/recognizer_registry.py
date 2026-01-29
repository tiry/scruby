"""Registry for Presidio recognizers."""

from typing import List

from presidio_analyzer import EntityRecognizer

from .custom_recognizers import (
    InsuranceIDRecognizer,
    MRNRecognizer,
    PrescriptionNumberRecognizer,
)


class RecognizerRegistry:
    """
    Registry for managing Presidio recognizers.
    
    Maintains a collection of custom recognizers that can be
    added to the Presidio analyzer.
    """
    
    def __init__(self):
        """Initialize the registry with default custom recognizers."""
        self._recognizers: List[EntityRecognizer] = []
        self._register_defaults()
    
    def _register_defaults(self) -> None:
        """Register default custom recognizers."""
        self.add_recognizer(MRNRecognizer())
        self.add_recognizer(PrescriptionNumberRecognizer())
        self.add_recognizer(InsuranceIDRecognizer())
    
    def add_recognizer(self, recognizer: EntityRecognizer) -> None:
        """
        Add a recognizer to the registry.
        
        Args:
            recognizer: EntityRecognizer instance to add
        """
        self._recognizers.append(recognizer)
    
    def get_all_recognizers(self) -> List[EntityRecognizer]:
        """Get all registered recognizers."""
        return self._recognizers.copy()
    
    def clear(self) -> None:
        """Clear all recognizers from the registry."""
        self._recognizers.clear()


# Singleton instance
_recognizer_registry = RecognizerRegistry()


def get_recognizer_registry() -> RecognizerRegistry:
    """Get the global recognizer registry instance."""
    return _recognizer_registry
