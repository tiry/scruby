"""Reader components for scruby."""

from .base import Reader, ReaderError
from .registry import get_reader_registry, reader_registry
from .text_file import TextFileReader

__all__ = [
    "Reader",
    "ReaderError",
    "reader_registry",
    "get_reader_registry",
    "TextFileReader",
]
