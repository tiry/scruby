"""Postprocessor components for scruby."""

from .base import Postprocessor, PostprocessorError
from .format_preserver import FormatPreserver
from .redaction_cleaner import RedactionCleaner
from .dict_merger import DictMergerPostprocessor
from .registry import get_postprocessor_registry, postprocessor_registry

__all__ = [
    "Postprocessor",
    "PostprocessorError",
    "RedactionCleaner",
    "FormatPreserver",
    "DictMergerPostprocessor",
    "postprocessor_registry",
    "get_postprocessor_registry",
]
