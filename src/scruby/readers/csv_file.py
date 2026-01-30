"""CSV file reader for structured data."""

import csv
from pathlib import Path
from typing import Any, Dict, Iterator

from .base import Reader
from .registry import reader_registry


@reader_registry.register_decorator("csv_file")
class CSVReader(Reader):
    """
    Reader for CSV files.
    
    Reads CSV files row-by-row, treating first row as headers.
    Each row becomes a dictionary with column names as keys.
    """
    
    def __init__(
        self,
        path: str | Path,
        config: Dict[str, Any] | None = None
    ):
        """
        Initialize CSV reader.
        
        Args:
            path: Path to CSV file
            config: Optional configuration dictionary
        """
        self.source_path = Path(path)
        
        # Extract CSV-specific config
        csv_config = config.get("readers", {}).get("csv_file", {}) if config else {}
        self.delimiter = csv_config.get("delimiter", ",")
        self.quotechar = csv_config.get("quotechar", '"')
        self.encoding = csv_config.get("encoding", "utf-8")
        self.skip_empty_rows = csv_config.get("skip_empty_rows", True)
    
    def read(self) -> Iterator[Dict[str, Any]]:
        """
        Read CSV file row-by-row.
        
        Yields:
            Dictionary for each row with metadata
        """
        if not self.source_path.exists():
            raise FileNotFoundError(f"CSV file not found: {self.source_path}")
        
        with open(self.source_path, 'r', encoding=self.encoding, newline='') as f:
            reader = csv.DictReader(
                f,
                delimiter=self.delimiter,
                quotechar=self.quotechar
            )
            
            for row_num, row_data in enumerate(reader, start=2):  # Row 2 is first data row
                # Skip empty rows if configured
                if self.skip_empty_rows and all(not v or not str(v).strip() for v in row_data.values()):
                    continue
                
                # Clean up None values (empty fields become empty strings)
                cleaned_data = {
                    key: (value if value is not None else "")
                    for key, value in row_data.items()
                }
                
                yield {
                    "content": None,  # Will be populated by preprocessor
                    "metadata": {
                        "source": str(self.source_path),
                        "row_number": row_num,
                        "original_data": cleaned_data
                    }
                }
