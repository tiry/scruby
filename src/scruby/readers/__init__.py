"""Reader components for scruby."""

from .base import Reader, ReaderError
from .registry import get_reader_registry, reader_registry
from .text_file import TextFileReader
from .csv_file import CSVReader
from .xlsx_file import XLSXReader

__all__ = [
    "Reader",
    "ReaderError",
    "reader_registry",
    "get_reader_registry",
    "TextFileReader",
    "CSVReader",
    "XLSXReader",
]
