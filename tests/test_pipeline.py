"""Tests for the pipeline orchestrator."""

import tempfile
from pathlib import Path

import pytest

from scruby.pipeline import Pipeline, PipelineError


class TestPipelineInitialization:
    """Tests for pipeline initialization."""

    def test_pipeline_initialization(self):
        """Verify pipeline initializes correctly."""
        pipeline = Pipeline()
        
        assert pipeline.config is not None
        assert pipeline.reader_registry is not None
        assert pipeline.preprocessor_registry is not None
        assert pipeline.postprocessor_registry is not None
        assert pipeline.writer_registry is not None
        assert pipeline.redactor is not None

    def test_pipeline_with_config(self):
        """Initialize with custom configuration."""
        config = {"redaction_strategy": "mask"}
        pipeline = Pipeline(config=config)
        
        assert pipeline.config == config


@pytest.mark.slow
class TestPipelineFlow:
    """Tests for complete pipeline flow."""

    def test_process_single_file(self, tmp_path):
        """Process single file through pipeline."""
        # Create input file
        input_file = tmp_path / "input.txt"
        input_file.write_text("Contact john.doe@example.com for info")
        
        output_file = tmp_path / "output.txt"
        
        pipeline = Pipeline()
        results = pipeline.process(
            input_path=str(input_file),
            output_path=str(output_file)
        )
        
        assert len(results) == 1
        assert "content" in results[0]
        assert "metadata" in results[0]
        assert output_file.exists()

    def test_process_with_preprocessors(self, tmp_path):
        """Apply preprocessors in pipeline."""
        input_file = tmp_path / "input.txt"
        input_file.write_text("Test  content   with    extra    spaces")
        
        output_file = tmp_path / "output.txt"
        
        pipeline = Pipeline()
        results = pipeline.process(
            input_path=str(input_file),
            output_path=str(output_file),
            preprocessors=["whitespace_normalizer"]
        )
        
        assert len(results) == 1
        # Whitespace should be normalized
        assert "    " not in results[0]["content"]

    def test_process_with_postprocessors(self, tmp_path):
        """Apply postprocessors in pipeline."""
        input_file = tmp_path / "input.txt"
        input_file.write_text("Email: test@example.com and another@example.com")
        
        output_file = tmp_path / "output.txt"
        
        pipeline = Pipeline()
        results = pipeline.process(
            input_path=str(input_file),
            output_path=str(output_file),
            postprocessors=["redaction_cleaner"]
        )
        
        assert len(results) == 1
        assert "content" in results[0]

    def test_process_complete_flow(self, tmp_path):
        """Full pipeline with all stages."""
        input_file = tmp_path / "input.txt"
        input_file.write_text("Contact  john.doe@example.com  for  info  .")
        
        output_file = tmp_path / "output.txt"
        
        pipeline = Pipeline()
        results = pipeline.process(
            input_path=str(input_file),
            output_path=str(output_file),
            preprocessors=["whitespace_normalizer"],
            postprocessors=["redaction_cleaner"]
        )
        
        assert len(results) == 1
        assert results[0]["metadata"]["redacted_entities"] >= 0
        assert output_file.exists()


class TestComponentIntegration:
    """Tests for component integration."""

    def test_reader_integration(self, tmp_path):
        """Verify reader works in pipeline."""
        input_file = tmp_path / "test.txt"
        input_file.write_text("Test content")
        
        pipeline = Pipeline()
        results = pipeline.process(
            input_path=str(input_file),
            output_path=None,
            writer_type="stdout"
        )
        
        assert len(results) == 1
        assert results[0]["content"] == "Test content"

    def test_redactor_integration(self, tmp_path):
        """Verify redactor works in pipeline."""
        input_file = tmp_path / "test.txt"
        input_file.write_text("Email: test@example.com")
        
        pipeline = Pipeline()
        results = pipeline.process(
            input_path=str(input_file),
            output_path=None,
            writer_type="stdout"
        )
        
        assert len(results) == 1
        # Email should be redacted
        assert "test@example.com" not in results[0]["content"]
        assert "redacted_entities" in results[0]["metadata"]

    def test_writer_integration(self, tmp_path):
        """Verify writer works in pipeline."""
        input_file = tmp_path / "test.txt"
        input_file.write_text("Test content")
        
        output_file = tmp_path / "output.txt"
        
        pipeline = Pipeline()
        results = pipeline.process(
            input_path=str(input_file),
            output_path=str(output_file),
            writer_type="text_file"
        )
        
        assert len(results) == 1
        assert output_file.exists()
        assert output_file.read_text() == "Test content"


class TestErrorHandling:
    """Tests for error handling."""

    def test_invalid_reader_type(self, tmp_path):
        """Handle unknown reader type."""
        input_file = tmp_path / "test.txt"
        input_file.write_text("Test")
        
        pipeline = Pipeline()
        
        with pytest.raises(PipelineError):
            pipeline.process(
                input_path=str(input_file),
                reader_type="invalid_reader"
            )

    def test_invalid_input_path(self):
        """Handle missing input file."""
        pipeline = Pipeline()
        
        with pytest.raises(PipelineError):
            pipeline.process(input_path="/nonexistent/file.txt")

    def test_pipeline_error_handling(self, tmp_path):
        """Handle processing errors gracefully."""
        # Create invalid scenario
        input_file = tmp_path / "test.txt"
        input_file.write_text("Test")
        
        pipeline = Pipeline()
        
        # Try to use invalid preprocessor
        with pytest.raises(PipelineError):
            pipeline.process(
                input_path=str(input_file),
                preprocessors=["nonexistent_preprocessor"]
            )
