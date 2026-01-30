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


class TestSnapshotComparison:
    """Test output consistency with snapshot comparison."""
    
    def test_snapshot_output_matches_expected(self, tmp_path):
        """Test that redaction output matches the expected snapshot."""
        # Use static test files
        input_file = TEST_DATA_DIR / "snapshot_input.txt"
        expected_file = TEST_DATA_DIR / "snapshot_expected.txt"
        output_file = tmp_path / "snapshot_output.txt"
        
        # Use fixed config for deterministic hashing
        config_path = TEST_DATA_DIR.parent / "fixtures" / "snapshot_config.yaml"
        config = load_config(config_path)
        pipeline = Pipeline(config=config)
        
        # Process the input
        results = pipeline.process(
            input_path=str(input_file),
            output_path=str(output_file),
            reader_type="text_file",
            writer_type="text_file"
        )
        
        # Read actual and expected outputs
        actual_output = output_file.read_text()
        expected_output = expected_file.read_text()
        
        # Compare outputs with detailed diff if they don't match
        if actual_output != expected_output:
            import difflib
            
            # Generate line-by-line diff
            expected_lines = expected_output.splitlines(keepends=True)
            actual_lines = actual_output.splitlines(keepends=True)
            
            diff = difflib.unified_diff(
                expected_lines,
                actual_lines,
                fromfile='expected',
                tofile='actual',
                lineterm=''
            )
            
            diff_text = '\n'.join(diff)
            
            # Also show character-level comparison for debugging
            error_msg = [
                "\n" + "=" * 80,
                "SNAPSHOT TEST FAILED - Output doesn't match expected!",
                "=" * 80,
                "\nUnified Diff:",
                diff_text,
                "\n" + "-" * 80,
                f"\nExpected length: {len(expected_output)} chars",
                f"Actual length:   {len(actual_output)} chars",
                "\n" + "-" * 80,
                "\nTo update the snapshot, run:",
                f"  cp {output_file} {expected_file}",
                "=" * 80
            ]
            
            pytest.fail('\n'.join(error_msg))
        
        # Verify we actually redacted something
        assert len(results) == 1
        assert results[0]["metadata"]["redacted_entities"] > 0


class TestEdgeCaseIntegration:
    """Integration tests for edge cases and error conditions."""
    
    def test_empty_file_processing(self, tmp_path):
        """Test processing an empty file."""
        # Create empty input file
        input_file = tmp_path / "empty.txt"
        input_file.write_text("")
        output_file = tmp_path / "output.txt"
        
        # Process file
        pipeline = Pipeline()
        results = pipeline.process(
            input_path=str(input_file),
            output_path=str(output_file),
            reader_type="text_file",
            writer_type="text_file"
        )
        
        # Verify results
        assert len(results) == 1
        assert results[0]["content"] == ""
        assert output_file.exists()
    
    def test_file_with_only_redactions(self, tmp_path):
        """Test file containing only PII data."""
        # Create file with multiple emails
        input_file = tmp_path / "pii_only.txt"
        input_file.write_text("john@example.com jane@example.com admin@example.com")
        output_file = tmp_path / "output.txt"
        
        # Process file
        pipeline = Pipeline()
        results = pipeline.process(
            input_path=str(input_file),
            output_path=str(output_file),
            reader_type="text_file",
            writer_type="text_file"
        )
        
        # Verify all emails were redacted
        assert len(results) == 1
        output_text = output_file.read_text()
        assert "john@example.com" not in output_text
        assert "jane@example.com" not in output_text
        assert "admin@example.com" not in output_text
        # Should have hash markers
        assert "<EMAIL_ADDRESS:" in output_text
    
    def test_mixed_content_with_special_characters(self, tmp_path):
        """Test file with special characters and unicode."""
        input_file = tmp_path / "special.txt"
        input_file.write_text("Patient: José García\nEmail: jose@example.com\n© 2024 Hospital™")
        output_file = tmp_path / "output.txt"
        
        # Process file
        pipeline = Pipeline()
        results = pipeline.process(
            input_path=str(input_file),
            output_path=str(output_file),
            reader_type="text_file",
            writer_type="text_file"
        )
        
        # Verify processing succeeded
        assert len(results) == 1
        assert output_file.exists()
        output_text = output_file.read_text()
        # Special characters should be preserved
        assert "©" in output_text or "Hospital" in output_text
        # Email should be redacted
        assert "jose@example.com" not in output_text


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
