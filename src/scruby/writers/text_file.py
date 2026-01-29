"""Text file writer implementation."""

from pathlib import Path
from typing import Any, Dict

from .base import Writer, WriterError
from .registry import writer_registry


@writer_registry.register_decorator("text_file")
class TextFileWriter(Writer):
    """
    Writer for plain text files.

    Can write to a single file or to a directory (using document metadata).
    """

    def __init__(self, path: str | Path, encoding: str = "utf-8"):
        """
        Initialize the text file writer.

        Args:
            path: Path to output file or directory
            encoding: Text encoding (default: utf-8)
        """
        # Check for trailing slash before converting to Path (Path normalizes it away)
        path_str = str(path)
        has_trailing_slash = path_str.endswith("/")
        
        self.path = Path(path)
        self.encoding = encoding
        self.is_directory = False

        # Determine if path should be treated as directory
        if self.path.exists() and self.path.is_dir():
            self.is_directory = True
        elif has_trailing_slash:
            self.is_directory = True
            self.path.mkdir(parents=True, exist_ok=True)

    def write(self, document: Dict[str, Any]) -> None:
        """
        Write document to file.

        Args:
            document: Document with 'content' and optional 'metadata' keys

        Raises:
            WriterError: If writing fails
        """
        if "content" not in document:
            raise WriterError("Document must contain 'content' key")

        try:
            if self.is_directory:
                self._write_to_directory(document)
            else:
                self._write_to_file(document)
        except WriterError:
            # Re-raise WriterError as is
            raise
        except Exception as e:
            raise WriterError(f"Failed to write document: {e}") from e

    def _write_to_file(self, document: Dict[str, Any]) -> None:
        """Write to a single file."""
        # Create parent directory if needed
        self.path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.path, "w", encoding=self.encoding) as f:
            f.write(document["content"])

    def _write_to_directory(self, document: Dict[str, Any]) -> None:
        """Write to directory using filename from metadata."""
        metadata = document.get("metadata", {})
        filename = metadata.get("filename")

        if not filename:
            raise WriterError(
                "Document metadata must contain 'filename' when writing to directory"
            )

        output_path = self.path / filename
        with open(output_path, "w", encoding=self.encoding) as f:
            f.write(document["content"])
