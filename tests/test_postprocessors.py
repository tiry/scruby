"""Tests for postprocessor components."""

import pytest

from scruby.postprocessors import (
    FormatPreserver,
    Postprocessor,
    RedactionCleaner,
    get_postprocessor_registry,
)


class TestPostprocessorBaseClass:
    """Tests for the postprocessor base class."""

    def test_postprocessor_is_abstract(self):
        """Postprocessor should be abstract and cannot be instantiated."""
        with pytest.raises(TypeError):
            Postprocessor()

    def test_postprocessor_requires_process_method(self):
        """Concrete postprocessors must implement process method."""
        
        class IncompletePostprocessor(Postprocessor):
            pass
        
        with pytest.raises(TypeError):
            IncompletePostprocessor()


class TestPostprocessorRegistry:
    """Tests for the postprocessor registry."""

    def test_postprocessor_registry_exists(self):
        """Postprocessor registry should be available."""
        registry = get_postprocessor_registry()
        assert registry is not None
        assert registry._component_type == "postprocessor"

    def test_redaction_cleaner_registered(self):
        """RedactionCleaner should be registered."""
        registry = get_postprocessor_registry()
        assert registry.is_registered("redaction_cleaner")

    def test_format_preserver_registered(self):
        """FormatPreserver should be registered."""
        registry = get_postprocessor_registry()
        assert registry.is_registered("format_preserver")

    def test_create_postprocessor_from_registry(self):
        """Should be able to create postprocessors from registry."""
        registry = get_postprocessor_registry()
        cleaner = registry.create("redaction_cleaner")
        assert isinstance(cleaner, RedactionCleaner)


class TestRedactionCleaner:
    """Tests for RedactionCleaner."""

    def test_merge_consecutive_redactions(self):
        """Should merge consecutive [REDACTED] tokens."""
        cleaner = RedactionCleaner()
        document = {
            "content": "Contact [REDACTED] [REDACTED] [REDACTED] for more info",
            "metadata": {"source": "test"}
        }
        
        result = cleaner.process(document)
        
        # Should merge into single [REDACTED]
        assert result["content"].count("[REDACTED]") == 1
        assert "[REDACTED] [REDACTED]" not in result["content"]

    def test_clean_extra_spaces(self):
        """Should remove extra whitespace."""
        cleaner = RedactionCleaner()
        document = {"content": "This  has    extra     spaces"}
        
        result = cleaner.process(document)
        
        assert result["content"] == "This has extra spaces"

    def test_fix_punctuation_spacing(self):
        """Should fix spacing around punctuation."""
        cleaner = RedactionCleaner()
        document = {"content": "Hello world , how are you ?"}
        
        result = cleaner.process(document)
        
        assert result["content"] == "Hello world, how are you?"

    def test_metadata_preserved(self):
        """Should preserve original metadata."""
        cleaner = RedactionCleaner()
        document = {
            "content": "Test content",
            "metadata": {"source": "file.txt", "author": "John"}
        }
        
        result = cleaner.process(document)
        
        assert result["metadata"]["source"] == "file.txt"
        assert result["metadata"]["author"] == "John"

    def test_no_merge_when_disabled(self):
        """Should not merge consecutive redactions when disabled."""
        cleaner = RedactionCleaner(merge_consecutive=False)
        document = {"content": "[REDACTED] [REDACTED]"}
        
        result = cleaner.process(document)
        
        # Should still have 2 after cleaning spaces
        assert result["content"] == "[REDACTED] [REDACTED]"


class TestFormatPreserver:
    """Tests for FormatPreserver."""

    def test_preserve_paragraphs(self):
        """Should maintain paragraph structure."""
        preserver = FormatPreserver()
        document = {"content": "Paragraph one.\n\nParagraph two."}
        
        result = preserver.process(document)
        
        # Content should remain unchanged
        assert result["content"] == "Paragraph one.\n\nParagraph two."

    def test_preserve_line_structure(self):
        """Should keep line structure intact."""
        preserver = FormatPreserver()
        document = {"content": "Line 1\nLine 2\nLine 3"}
        
        result = preserver.process(document)
        
        assert "Line 1" in result["content"]
        assert "Line 2" in result["content"]
        assert "Line 3" in result["content"]

    def test_metadata_preserved(self):
        """Should preserve original metadata."""
        preserver = FormatPreserver()
        document = {
            "content": "Test",
            "metadata": {"format": "plain", "lines": 5}
        }
        
        result = preserver.process(document)
        
        assert result["metadata"]["format"] == "plain"
        assert result["metadata"]["lines"] == 5


class TestPostprocessorErrorHandling:
    """Tests for error handling."""

    def test_missing_content_key(self):
        """Should handle documents without content key."""
        cleaner = RedactionCleaner()
        document = {"metadata": {"source": "test"}}
        
        # Should raise KeyError
        with pytest.raises(KeyError):
            cleaner.process(document)

    def test_postprocessor_chaining(self):
        """Should be able to chain multiple postprocessors."""
        cleaner = RedactionCleaner()
        preserver = FormatPreserver()
        
        document = {
            "content": "[REDACTED]  [REDACTED]  text",
            "metadata": {"source": "test"}
        }
        
        # Apply cleaner first
        result1 = cleaner.process(document)
        # Then apply preserver
        result2 = preserver.process(result1)
        
        # Should have both transformations applied
        assert result2["content"] != document["content"]
        
        # Should have both transformations applied
        assert result2["content"] != document["content"]


class TestPostprocessorEdgeCases:
    """Tests for edge cases in postprocessors."""

    def test_redaction_cleaner_empty_string(self):
        """Handle empty string input."""
        cleaner = RedactionCleaner()
        document = {"content": ""}
        
        result = cleaner.process(document)
        
        assert result["content"] == ""
    
    def test_redaction_cleaner_no_redactions(self):
        """Handle text with no redaction markers."""
        cleaner = RedactionCleaner()
        document = {"content": "Normal text without any redactions"}
        
        result = cleaner.process(document)
        
        assert result["content"] == "Normal text without any redactions"
    
    def test_redaction_cleaner_only_redactions(self):
        """Handle text that is entirely redacted."""
        cleaner = RedactionCleaner()
        document = {"content": "[REDACTED] [REDACTED] [REDACTED]"}
        
        result = cleaner.process(document)
        
        # Should merge all consecutive redactions
        assert result["content"].count("[REDACTED]") == 1
    
    def test_format_preserver_empty_metadata(self):
        """Handle document with no metadata."""
        preserver = FormatPreserver()
        document = {"content": "Test content"}
        
        result = preserver.process(document)
        
        # FormatPreserver doesn't add metadata, it only preserves format info
        # Just verify it doesn't crash
        assert result["content"] == "Test content"
    
    def test_format_preserver_multiline_empty(self):
        """Handle empty multiline content."""
        preserver = FormatPreserver()
        document = {"content": "", "metadata": {}}
        
        result = preserver.process(document)
        
        # Verify it processes without error
        assert result["content"] == ""
