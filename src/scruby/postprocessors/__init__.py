"""Postprocessor components for scruby."""

from .base import Postprocessor
from .format_preserver import FormatPreserver
from .redaction_cleaner import RedactionCleaner
from .registry import get_postprocessor_registry

# Register postprocessors
get_postprocessor_registry().register("redaction_cleaner", RedactionCleaner)
get_postprocessor_registry().register("format_preserver", FormatPreserver)

__all__ = [
    "Postprocessor",
    "RedactionCleaner",
    "FormatPreserver",
    "get_postprocessor_registry",
]
