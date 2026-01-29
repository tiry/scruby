"""Presidio integration for scruby."""

from .analyzer_wrapper import PresidioAnalyzer, PresidioAnalyzerError
from .custom_recognizers import (
    InsuranceIDRecognizer,
    MRNRecognizer,
    PrescriptionNumberRecognizer,
)
from .recognizer_registry import RecognizerRegistry, get_recognizer_registry

__all__ = [
    "PresidioAnalyzer",
    "PresidioAnalyzerError",
    "MRNRecognizer",
    "PrescriptionNumberRecognizer",
    "InsuranceIDRecognizer",
    "RecognizerRegistry",
    "get_recognizer_registry",
]
