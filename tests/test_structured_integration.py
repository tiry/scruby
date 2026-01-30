"""Integration tests for structured data (CSV/XLSX) redaction."""

import tempfile
from pathlib import Path

import pytest

from scruby.config import load_config
from scruby.pipeline import Pipeline


class TestStructuredDataRedaction:
    """Test end-to-end structured data redaction."""
    
    def test_csv_redaction_with_field_selector(self):
        """Test CSV redaction with field selection."""
        
        # Load configuration from YAML file
        config = load_config("tests/fixtures/structured_config.yaml")
        
        input_file = Path("tests/data/test_patients.csv")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=".csv", delete=False) as tmp:
            output_file = Path(tmp.name)
        
        try:
            pipeline = Pipeline(config=config)
            
            processed_docs = pipeline.process(
                input_path=input_file,
                output_path=output_file,
                reader_type="csv_file",
                writer_type="csv_file",
                preprocessors=["field_selector"],
                postprocessors=["dict_merger"]
            )
            
            # Verify processing
            assert len(processed_docs) == 3, "Should process 3 rows"
            
            # Read and verify output
            import csv
            with open(output_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            assert len(rows) == 3, "Output should have 3 rows"
            
            # Check basic structure
            for row in rows:
                # All expected fields should be present
                assert "ID" in row, "ID field should exist"
                assert "Name" in row, "Name field should exist"
                assert "Email" in row, "Email field should exist"
                assert "SSN" in row, "SSN field should exist"
                assert "Phone" in row, "Phone field should exist"
            
            print(f"\n✅ CSV test passed - {len(rows)} rows processed with correct structure")
            
        finally:
            if output_file.exists():
                output_file.unlink()
    
    def test_hash_consistency_across_rows(self):
        """Verify that same PII values get same hash across different rows."""
        
        # Load configuration from YAML file
        config = load_config("tests/fixtures/hash_consistency_config.yaml")
        
        # Create temp CSV with duplicate emails
        import csv
        with tempfile.NamedTemporaryFile(mode='w', suffix=".csv", delete=False, newline='') as tmp_in:
            input_file = Path(tmp_in.name)
            writer = csv.DictWriter(tmp_in, fieldnames=["ID", "Email"])
            writer.writeheader()
            writer.writerow({"ID": "1", "Email": "test@example.com"})
            writer.writerow({"ID": "2", "Email": "test@example.com"})  # Same email
            writer.writerow({"ID": "3", "Email": "other@example.com"})  # Different email
        
        with tempfile.NamedTemporaryFile(mode='w', suffix=".csv", delete=False) as tmp_out:
            output_file = Path(tmp_out.name)
        
        try:
            pipeline = Pipeline(config=config)
            
            pipeline.process(
                input_path=input_file,
                output_path=output_file,
                reader_type="csv_file",
                writer_type="csv_file",
                preprocessors=["field_selector"],
                postprocessors=["dict_merger"]
            )
            
            # Read output
            with open(output_file, 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
            
            # Verify same email gets same hash
            assert rows[0]["Email"] == rows[1]["Email"], \
                "Same email should have same redacted hash"
            
            assert rows[0]["Email"] != rows[2]["Email"], \
                "Different emails should have different hashes"
            
            print(f"\n✅ Hash consistency verified")
            print(f"  Same email hash: {rows[0]['Email']}")
            print(f"  Different email hash: {rows[2]['Email']}")
            
        finally:
            if input_file.exists():
                input_file.unlink()
            if output_file.exists():
                output_file.unlink()


if __name__ == "__main__":
    # Run tests
    test = TestStructuredDataRedaction()
    
    print("=" * 60)
    print("Testing CSV Redaction")
    print("=" * 60)
    test.test_csv_redaction_with_field_selector()
    
    print("\n" + "=" * 60)
    print("Testing Hash Consistency")
    print("=" * 60)
    test.test_hash_consistency_across_rows()
    
    print("\n" + "=" * 60)
    print("✅ ALL TESTS PASSED!")
    print("=" * 60)
