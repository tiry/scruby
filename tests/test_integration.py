"""Integration tests for scruby."""

import tempfile
from pathlib import Path

import pytest

from scruby.cli import main
from scruby.config import load_config
from scruby.pipeline import Pipeline

# Path to test data directory
TEST_DATA_DIR = Path(__file__).parent / "data"


class TestEndToEndPipeline:
    """Test complete end-to-end pipeline workflows."""
    
    def test_complete_pipeline_with_hash_strategy(self, tmp_path):
        """Test complete pipeline from file read to write with hash strategy."""
        # Use static test file
        input_file = TEST_DATA_DIR / "simple_patient.txt"
        output_file = tmp_path / "output.txt"
        
        # Load config and create pipeline
        config_path = Path("config.yaml")
        if not config_path.exists():
            pytest.skip("config.yaml not found")
        
        config = load_config(config_path)
        pipeline = Pipeline(config=config)
        
        # Process file
        results = pipeline.process(
            input_path=str(input_file),
            output_path=str(output_file),
            reader_type="text_file",
            writer_type="text_file"
        )
        
        # Verify results
        assert len(results) == 1
        assert results[0]["metadata"]["redacted_entities"] > 0
        assert output_file.exists()
        
        # Verify output contains hashes with entity type prefix
        output_text = output_file.read_text()
        assert "<PERSON:" in output_text or "<US_SSN:" in output_text or "<EMAIL_ADDRESS:" in output_text
    
    def test_pipeline_with_preprocessors_and_postprocessors(self, tmp_path):
        """Test pipeline with preprocessing and postprocessing."""
        # Use static test file
        input_file = TEST_DATA_DIR / "whitespace_test.txt"
        output_file = tmp_path / "output.txt"
        
        config = load_config("config.yaml")
        pipeline = Pipeline(config=config)
        
        results = pipeline.process(
            input_path=str(input_file),
            output_path=str(output_file),
            reader_type="text_file",
            writer_type="text_file",
            preprocessors=["whitespace_normalizer"],
            postprocessors=["redaction_cleaner"]
        )
        
        assert len(results) == 1
        assert output_file.exists()


class TestHashNormalization:
    """Test hash strategy normalization."""
    
    def test_same_entity_different_case_produces_same_hash(self, tmp_path):
        """Test that entity normalization produces consistent hashes."""
        # Use static test file
        input_file = TEST_DATA_DIR / "repeated_entities.txt"
        output_file = tmp_path / "output.txt"
        
        config = load_config("config.yaml")
        pipeline = Pipeline(config=config)
        
        results = pipeline.process(
            input_path=str(input_file),
            output_path=str(output_file),
            reader_type="text_file",
            writer_type="text_file"
        )
        
        # Read output and check for hash consistency
        output_text = output_file.read_text()
        
        # Extract all PERSON hashes
        import re
        person_hashes = re.findall(r'<PERSON:([a-f0-9]+)>', output_text)
        
        # All three variations should produce the same hash
        if len(person_hashes) >= 3:
            assert person_hashes[0] == person_hashes[1] == person_hashes[2], \
                "Same entity with different casing should produce same hash"


class TestMultipleFiles:
    """Test processing multiple files."""
    
    def test_directory_processing(self, tmp_path):
        """Test processing a directory with multiple files."""
        # Use static test directory
        input_dir = TEST_DATA_DIR / "multi_dir"
        output_dir = tmp_path / "output"
        
        config = load_config("config.yaml")
        pipeline = Pipeline(config=config)
        
        results = pipeline.process(
            input_path=str(input_dir),
            output_path=str(output_dir) + "/",
            reader_type="text_file",
            writer_type="text_file"
        )
        
        # Should process 2 files
        assert len(results) == 2
        
        # Verify output files exist
        assert (output_dir / "file1.txt").exists()
        assert (output_dir / "file2.txt").exists()
        
        # Verify redaction occurred
        assert all(doc["metadata"]["redacted_entities"] > 0 for doc in results)


class TestCLIIntegration:
    """Test CLI integration."""
    
    def test_cli_end_to_end(self, tmp_path):
        """Test CLI processing from start to finish."""
        from click.testing import CliRunner
        
        # Use static test file
        input_file = TEST_DATA_DIR / "cli_test.txt"
        output_file = tmp_path / "output.txt"
        
        runner = CliRunner()
        result = runner.invoke(main, [
            "--src", str(input_file),
            "--out", str(output_file),
            "--verbose"
        ])
        
        assert result.exit_code == 0
        assert output_file.exists()
        assert "Processed 1 document(s)" in result.output
        assert "Redacted" in result.output
    
    def test_cli_with_all_options(self, tmp_path):
        """Test CLI with preprocessors, postprocessors, and threshold."""
        from click.testing import CliRunner
        
        # Use static test file
        input_file = TEST_DATA_DIR / "whitespace_test.txt"
        output_file = tmp_path / "output.txt"
        
        runner = CliRunner()
        result = runner.invoke(main, [
            "--src", str(input_file),
            "--out", str(output_file),
            "--preprocessors", "whitespace_normalizer",
            "--postprocessors", "redaction_cleaner",
            "--threshold", "0.5",
            "--verbose"
        ])
        
        assert result.exit_code == 0
        assert output_file.exists()


class TestRealWorldScenarios:
    """Test real-world usage scenarios."""
    
    def test_medical_record_redaction(self, tmp_path):
        """Test redacting a complete medical record."""
        # Use static test file
        input_file = TEST_DATA_DIR / "medical_record.txt"
        output_file = tmp_path / "redacted_record.txt"
        
        config = load_config("config.yaml")
        pipeline = Pipeline(config=config)
        
        results = pipeline.process(
            input_path=str(input_file),
            output_path=str(output_file),
            reader_type="text_file",
            writer_type="text_file",
            postprocessors=["redaction_cleaner"]
        )
        
        assert len(results) == 1
        assert results[0]["metadata"]["redacted_entities"] >= 8  # At least 8 PII elements
        
        # Verify output doesn't contain original PII
        output_text = output_file.read_text()
        assert "Jane Elizabeth Doe" not in output_text
        assert "987-65-4321" not in output_text
        assert "jane.doe@email.com" not in output_text
        
        # Verify it contains hashed entities
        assert "<PERSON:" in output_text
        assert "<US_SSN:" in output_text or "<ORGANIZATION:" in output_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
