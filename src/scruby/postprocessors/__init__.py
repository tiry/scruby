"""Postprocessor components for scruby."""

from .base import Postprocessor
from .format_preserver import FormatPreserver
from .redaction_cleaner import RedactionCleaner
from .registry import get_postprocessor_registry, postprocessor_registry

__all__ = [
    "Postprocessor",
    "RedactionCleaner",
    "FormatPreserver",
    "postprocessor_registry",
    "get_postprocessor_registry",
]
