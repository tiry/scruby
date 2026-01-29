"""Preprocessor components for scruby."""

from .base import Preprocessor, PreprocessorError
from .registry import get_preprocessor_registry, preprocessor_registry
from .text_cleaner import TextCleaner
from .whitespace import WhitespaceNormalizer

__all__ = [
    "Preprocessor",
    "PreprocessorError",
    "preprocessor_registry",
    "get_preprocessor_registry",
    "WhitespaceNormalizer",
    "TextCleaner",
]
