"""CSV file writer for structured data."""

import csv
from pathlib import Path
from typing import Any, Dict

from .base import Writer
from .registry import writer_registry


@writer_registry.register_decorator("csv_file")
class CSVWriter(Writer):
    """
    Writer for CSV files.
    
    Writes dictionary data to CSV format, preserving column order.
    """
    
    def __init__(
        self,
        path: str | Path,
        config: Dict[str, Any] | None = None
    ):
        """
        Initialize CSV writer.
        
        Args:
            path: Path to output CSV file
            config: Optional configuration dictionary
        """
        self.destination_path = Path(path)
        
        # Extract CSV-specific config
        csv_config = config.get("writers", {}).get("csv_file", {}) if config else {}
        self.delimiter = csv_config.get("delimiter", ",")
        self.quotechar = csv_config.get("quotechar", '"')
        self.encoding = csv_config.get("encoding", "utf-8")
        self.write_header = csv_config.get("write_header", True)
        
        # Track if header has been written
        self._header_written = False
        self._file_handle = None
        self._csv_writer = None
        self._fieldnames = None
    
    def write(self, document: Dict[str, Any]) -> None:
        """
        Write document as CSV row.
        
        Args:
            document: Document with redacted_data in metadata
        """
        # Get redacted data
        redacted_data = document.get("metadata", {}).get("redacted_data", {})
        
        if not redacted_data:
            return
        
        # Open file on first write
        if self._file_handle is None:
            self.destination_path.parent.mkdir(parents=True, exist_ok=True)
            self._file_handle = open(
                self.destination_path,
                'w',
                encoding=self.encoding,
                newline=''
            )
            
            # Get fieldnames from first document
            self._fieldnames = list(redacted_data.keys())
            
            self._csv_writer = csv.DictWriter(
                self._file_handle,
                fieldnames=self._fieldnames,
                delimiter=self.delimiter,
                quotechar=self.quotechar
            )
            
            # Write header if configured
            if self.write_header:
                self._csv_writer.writeheader()
                self._header_written = True
        
        # Write row
        self._csv_writer.writerow(redacted_data)
    
    def close(self) -> None:
        """Close the CSV file."""
        if self._file_handle:
            self._file_handle.close()
            self._file_handle = None
            self._csv_writer = None
    
    def __del__(self):
        """Ensure file is closed on deletion."""
        self.close()
