"""Text file reader implementation."""

from pathlib import Path
from typing import Any, Dict, Iterator

from .base import Reader, ReaderError
from .registry import reader_registry


@reader_registry.register_decorator("text_file")
class TextFileReader(Reader):
    """
    Reader for plain text files.

    Supports reading a single file or all .txt files in a directory.
    """

    def __init__(self, path: str | Path, encoding: str = "utf-8"):
        """
        Initialize the text file reader.

        Args:
            path: Path to a file or directory
            encoding: Text encoding (default: utf-8)
        """
        self.path = Path(path)
        self.encoding = encoding

        if not self.path.exists():
            raise ReaderError(f"Path not found: {self.path}")

    def read(self) -> Iterator[Dict[str, Any]]:
        """
        Read text file(s).

        Yields:
            Document dictionaries with 'content' and 'metadata' keys

        Raises:
            ReaderError: If reading fails
        """
        if self.path.is_file():
            yield from self._read_file(self.path)
        elif self.path.is_dir():
            yield from self._read_directory(self.path)
        else:
            raise ReaderError(f"Path is neither file nor directory: {self.path}")

    def _read_file(self, file_path: Path) -> Iterator[Dict[str, Any]]:
        """Read a single file."""
        try:
            with open(file_path, "r", encoding=self.encoding) as f:
                content = f.read()

            yield {
                "content": content,
                "metadata": {
                    "filename": file_path.name,
                    "path": str(file_path.absolute()),
                },
            }
        except Exception as e:
            raise ReaderError(f"Failed to read file {file_path}: {e}") from e

    def _read_directory(self, dir_path: Path) -> Iterator[Dict[str, Any]]:
        """Read all .txt files in a directory."""
        txt_files = sorted(dir_path.glob("*.txt"))

        if not txt_files:
            raise ReaderError(f"No .txt files found in directory: {dir_path}")

        for file_path in txt_files:
            yield from self._read_file(file_path)
