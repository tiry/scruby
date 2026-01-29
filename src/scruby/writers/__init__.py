"""Writer components for scruby."""

from .base import Writer, WriterError
from .registry import get_writer_registry, writer_registry
from .stdout import StdoutWriter
from .text_file import TextFileWriter

__all__ = [
    "Writer",
    "WriterError",
    "writer_registry",
    "get_writer_registry",
    "TextFileWriter",
    "StdoutWriter",
]
