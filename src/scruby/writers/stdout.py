"""Stdout writer implementation."""

import sys
from typing import Any, Dict

from .base import Writer, WriterError
from .registry import writer_registry


@writer_registry.register_decorator("stdout")
class StdoutWriter(Writer):
    """
    Writer that outputs to stdout.

    Useful for piping output or when no destination is specified.
    """

    def __init__(self, show_metadata: bool = False):
        """
        Initialize stdout writer.

        Args:
            show_metadata: If True, display metadata before content
        """
        self.show_metadata = show_metadata

    def write(self, document: Dict[str, Any]) -> None:
        """
        Write document to stdout.

        Args:
            document: Document with 'content' and optional 'metadata' keys

        Raises:
            WriterError: If writing fails
        """
        if "content" not in document:
            raise WriterError("Document must contain 'content' key")

        try:
            if self.show_metadata and "metadata" in document:
                metadata = document["metadata"]
                print(f"--- Metadata: {metadata} ---", file=sys.stdout)

            print(document["content"], file=sys.stdout)

        except Exception as e:
            raise WriterError(f"Failed to write to stdout: {e}") from e
