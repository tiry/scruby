"""Tests for CLI interface."""

import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from scruby.cli import main


@pytest.fixture
def cli_runner():
    """Create a CLI runner for testing."""
    return CliRunner()


@pytest.fixture
def sample_file(tmp_path):
    """Create a sample text file for testing."""
    file_path = tmp_path / "test_input.txt"
    file_path.write_text("John Doe lives at 123 Main St. Email: john@example.com")
    return file_path


@pytest.fixture
def output_file(tmp_path):
    """Create an output file path."""
    return tmp_path / "test_output.txt"


class TestBasicFunctionality:
    """Test basic CLI functionality."""
    
    def test_cli_help(self, cli_runner):
        """Test help message display."""
        result = cli_runner.invoke(main, ["--help"])
        assert result.exit_code == 0
        assert "Scruby - PII Redaction Tool" in result.output
        assert "--src" in result.output
        assert "--out" in result.output
    
    def test_cli_version(self, cli_runner):
        """Test version display."""
        result = cli_runner.invoke(main, ["--version"])
        assert result.exit_code == 0
        assert "scruby" in result.output
        assert "0.1.0" in result.output
    
    def test_cli_missing_src(self, cli_runner):
        """Test error when --src not provided."""
        result = cli_runner.invoke(main, [])
        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()


class TestFileProcessing:
    """Test file processing operations."""
    
    def test_cli_single_file_to_stdout(self, cli_runner, sample_file):
        """Test processing file to stdout."""
        result = cli_runner.invoke(main, ["--src", str(sample_file)])
        assert result.exit_code == 0
        # Output should contain redacted content
        assert len(result.output) > 0
    
    def test_cli_single_file_to_file(self, cli_runner, sample_file, output_file):
        """Test processing file to file."""
        result = cli_runner.invoke(main, [
            "--src", str(sample_file),
            "--out", str(output_file)
        ])
        assert result.exit_code == 0
        assert output_file.exists()
        
        # Check if output file has content
        output_content = output_file.read_text()
        assert len(output_content) > 0
    
    def test_cli_directory(self, cli_runner, tmp_path):
        """Test processing directory."""
        # Create input directory with files
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        (input_dir / "file1.txt").write_text("Test content 1")
        (input_dir / "file2.txt").write_text("Test content 2")
        
        # Create output directory
        output_dir = tmp_path / "output"
        output_dir.mkdir()
        
        result = cli_runner.invoke(main, [
            "--src", str(input_dir),
            "--out", str(output_dir)
        ])
        assert result.exit_code == 0


class TestOptions:
    """Test CLI options."""
    
    def test_cli_with_preprocessors(self, cli_runner, sample_file, output_file):
        """Test applying preprocessors."""
        result = cli_runner.invoke(main, [
            "--src", str(sample_file),
            "--out", str(output_file),
            "--preprocessors", "whitespace_normalizer"
        ])
        assert result.exit_code == 0
        assert output_file.exists()
    
    def test_cli_with_postprocessors(self, cli_runner, sample_file, output_file):
        """Test applying postprocessors."""
        result = cli_runner.invoke(main, [
            "--src", str(sample_file),
            "--out", str(output_file),
            "--postprocessors", "redaction_cleaner"
        ])
        assert result.exit_code == 0
        assert output_file.exists()
    
    def test_cli_with_multiple_preprocessors(self, cli_runner, sample_file, output_file):
        """Test applying multiple preprocessors."""
        result = cli_runner.invoke(main, [
            "--src", str(sample_file),
            "--out", str(output_file),
            "--preprocessors", "whitespace_normalizer,text_cleaner"
        ])
        assert result.exit_code == 0
        assert output_file.exists()
    
    def test_cli_with_threshold(self, cli_runner, sample_file, output_file):
        """Test overriding confidence threshold."""
        result = cli_runner.invoke(main, [
            "--src", str(sample_file),
            "--out", str(output_file),
            "--threshold", "0.8"
        ])
        assert result.exit_code == 0
        assert output_file.exists()
    
    def test_cli_invalid_threshold_low(self, cli_runner, sample_file):
        """Test rejecting threshold below 0.0."""
        result = cli_runner.invoke(main, [
            "--src", str(sample_file),
            "--threshold", "-0.1"
        ])
        assert result.exit_code == 1
        assert "Threshold must be between 0.0 and 1.0" in result.output
    
    def test_cli_invalid_threshold_high(self, cli_runner, sample_file):
        """Test rejecting threshold above 1.0."""
        result = cli_runner.invoke(main, [
            "--src", str(sample_file),
            "--threshold", "1.5"
        ])
        assert result.exit_code == 1
        assert "Threshold must be between 0.0 and 1.0" in result.output


class TestVerboseMode:
    """Test verbose output mode."""
    
    def test_cli_verbose_output(self, cli_runner, sample_file, output_file):
        """Test verbose mode displays processing information."""
        result = cli_runner.invoke(main, [
            "--src", str(sample_file),
            "--out", str(output_file),
            "--verbose"
        ])
        assert result.exit_code == 0
        assert "Processing:" in result.output
        assert "Output:" in result.output
        assert "Reader:" in result.output
        assert "Writer:" in result.output
        assert "Processed" in result.output
        assert "document(s)" in result.output
    
    def test_cli_verbose_with_preprocessors(self, cli_runner, sample_file, output_file):
        """Test verbose mode shows preprocessors."""
        result = cli_runner.invoke(main, [
            "--src", str(sample_file),
            "--out", str(output_file),
            "--preprocessors", "whitespace_normalizer",
            "--verbose"
        ])
        assert result.exit_code == 0
        assert "Preprocessors:" in result.output
        assert "whitespace_normalizer" in result.output


class TestErrorHandling:
    """Test error handling."""
    
    def test_cli_invalid_input_path(self, cli_runner):
        """Test handling of non-existent input path."""
        result = cli_runner.invoke(main, [
            "--src", "/nonexistent/path/file.txt"
        ])
        assert result.exit_code != 0
    
    def test_cli_invalid_reader(self, cli_runner, sample_file):
        """Test handling of unknown reader type."""
        result = cli_runner.invoke(main, [
            "--src", str(sample_file),
            "--reader", "nonexistent_reader"
        ])
        assert result.exit_code == 1
        assert "Pipeline error:" in result.output or "Error:" in result.output
    
    def test_cli_invalid_config_path(self, cli_runner, sample_file):
        """Test handling of non-existent config file."""
        result = cli_runner.invoke(main, [
            "--src", str(sample_file),
            "--config", "/nonexistent/config.yaml"
        ])
        assert result.exit_code != 0


class TestAutoDetection:
    """Test auto-detection features."""
    
    def test_auto_detect_stdout_writer(self, cli_runner, sample_file):
        """Test auto-detection of stdout writer when no output specified."""
        result = cli_runner.invoke(main, [
            "--src", str(sample_file),
            "--verbose"
        ])
        assert result.exit_code == 0
        assert "Writer: stdout" in result.output
    
    def test_auto_detect_file_writer(self, cli_runner, sample_file, output_file):
        """Test auto-detection of text_file writer when output specified."""
        result = cli_runner.invoke(main, [
            "--src", str(sample_file),
            "--out", str(output_file),
            "--verbose"
        ])
        assert result.exit_code == 0
        assert "Writer: text_file" in result.output


class TestShortOptions:
    """Test short option variants."""
    
    def test_short_src_option(self, cli_runner, sample_file):
        """Test -s short option for --src."""
        result = cli_runner.invoke(main, ["-s", str(sample_file)])
        assert result.exit_code == 0
    
    def test_short_out_option(self, cli_runner, sample_file, output_file):
        """Test -o short option for --out."""
        result = cli_runner.invoke(main, [
            "-s", str(sample_file),
            "-o", str(output_file)
        ])
        assert result.exit_code == 0
        assert output_file.exists()
    
    def test_short_verbose_option(self, cli_runner, sample_file):
        """Test -v short option for --verbose."""
        result = cli_runner.invoke(main, [
            "-s", str(sample_file),
            "-v"
        ])
        assert result.exit_code == 0
        assert "Processing:" in result.output
