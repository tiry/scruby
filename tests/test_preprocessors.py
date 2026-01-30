"""Tests for preprocessor components."""

import pytest

from scruby.preprocessors import (
    Preprocessor,
    PreprocessorError,
    WhitespaceNormalizer,
    TextCleaner,
    preprocessor_registry,
    get_preprocessor_registry,
)


class TestPreprocessorBaseClass:
    """Tests for the abstract Preprocessor base class."""

    def test_preprocessor_is_abstract(self):
        """Verify Preprocessor cannot be instantiated directly."""
        with pytest.raises(TypeError):
            Preprocessor()

    def test_preprocessor_requires_process_method(self):
        """Verify subclass must implement process() method."""

        class IncompletePreprocessor(Preprocessor):
            pass

        with pytest.raises(TypeError):
            IncompletePreprocessor()


class TestPreprocessorRegistry:
    """Tests for the preprocessor registry."""

    def test_preprocessor_registry_exists(self):
        """Verify registry is available."""
        assert preprocessor_registry is not None
        assert preprocessor_registry._component_type == "preprocessor"

    def test_get_preprocessor_registry(self):
        """Verify get_preprocessor_registry function works."""
        registry = get_preprocessor_registry()
        assert registry is preprocessor_registry

    def test_whitespace_normalizer_registered(self):
        """Verify WhitespaceNormalizer is auto-registered."""
        assert preprocessor_registry.is_registered("whitespace_normalizer")

    def test_text_cleaner_registered(self):
        """Verify TextCleaner is auto-registered."""
        assert preprocessor_registry.is_registered("text_cleaner")

    def test_create_preprocessor_from_registry(self):
        """Create preprocessor via factory."""
        preprocessor = preprocessor_registry.create("whitespace_normalizer")
        assert isinstance(preprocessor, WhitespaceNormalizer)


class TestWhitespaceNormalizer:
    """Tests for WhitespaceNormalizer."""

    def test_normalize_tabs_to_spaces(self):
        """Convert tabs to spaces."""
        preprocessor = WhitespaceNormalizer()
        document = {"content": "Hello\t\tWorld"}

        result = preprocessor.process(document)

        assert result["content"] == "Hello World"

    def test_normalize_multiple_spaces(self):
        """Convert multiple spaces to single."""
        preprocessor = WhitespaceNormalizer()
        document = {"content": "Hello    World   Test"}

        result = preprocessor.process(document)

        assert result["content"] == "Hello World Test"

    def test_normalize_line_breaks(self):
        """Normalize different line break types."""
        preprocessor = WhitespaceNormalizer(preserve_paragraphs=False)
        
        # Test \r\n
        doc1 = {"content": "Hello\r\nWorld"}
        result1 = preprocessor.process(doc1)
        assert "\r" not in result1["content"]
        
        # Test \r
        doc2 = {"content": "Hello\rWorld"}
        result2 = preprocessor.process(doc2)
        assert "\r" not in result2["content"]

    def test_preserve_paragraphs(self):
        """Keep paragraph breaks when enabled."""
        preprocessor = WhitespaceNormalizer(preserve_paragraphs=True)
        document = {"content": "Paragraph 1\n\nParagraph 2\n\n\nParagraph 3"}

        result = preprocessor.process(document)

        # Should have exactly 2 newlines between paragraphs
        assert "Paragraph 1\n\nParagraph 2\n\nParagraph 3" == result["content"]

    def test_dont_preserve_paragraphs(self):
        """Remove all extra whitespace when disabled."""
        preprocessor = WhitespaceNormalizer(preserve_paragraphs=False)
        document = {"content": "Line 1\n\nLine 2\n\n\nLine 3"}

        result = preprocessor.process(document)

        # Should collapse all whitespace to single space
        assert result["content"] == "Line 1 Line 2 Line 3"

    def test_strip_leading_trailing(self):
        """Remove leading/trailing whitespace."""
        preprocessor = WhitespaceNormalizer()
        document = {"content": "   Hello World   \n"}

        result = preprocessor.process(document)

        assert result["content"] == "Hello World"

    def test_metadata_preserved(self):
        """Metadata should be preserved through processing."""
        preprocessor = WhitespaceNormalizer()
        document = {
            "content": "Hello   World",
            "metadata": {"filename": "test.txt", "source": "test"}
        }

        result = preprocessor.process(document)

        assert result["metadata"] == {"filename": "test.txt", "source": "test"}
        assert result["content"] == "Hello World"


class TestTextCleaner:
    """Tests for TextCleaner."""

    def test_remove_control_characters(self):
        """Remove control characters."""
        preprocessor = TextCleaner()
        # Include a control character (bell character \x07)
        document = {"content": "Hello\x07World\x00Test"}

        result = preprocessor.process(document)

        assert result["content"] == "HelloWorldTest"

    def test_normalize_quotes(self):
        """Convert curly quotes to straight."""
        preprocessor = TextCleaner(normalize_quotes=True)
        document = {"content": "\u201cHello\u201d and \u2018World\u2019"}

        result = preprocessor.process(document)

        # Curly quotes should be normalized to straight quotes
        assert '"' in result["content"]
        assert "'" in result["content"]
        assert "\u201c" not in result["content"]
        assert "\u201d" not in result["content"]

    def test_no_normalize_quotes(self):
        """Keep curly quotes when disabled."""
        preprocessor = TextCleaner(normalize_quotes=False)
        document = {"content": "\u201cHello\u201d and \u2018World\u2019"}

        result = preprocessor.process(document)

        assert result["content"] == "\u201cHello\u201d and \u2018World\u2019"

    def test_lowercase_conversion(self):
        """Convert to lowercase when enabled."""
        preprocessor = TextCleaner(lowercase=True)
        document = {"content": "Hello WORLD Test"}

        result = preprocessor.process(document)

        assert result["content"] == "hello world test"

    def test_no_lowercase_conversion(self):
        """Keep case when disabled."""
        preprocessor = TextCleaner(lowercase=False)
        document = {"content": "Hello WORLD Test"}

        result = preprocessor.process(document)

        assert result["content"] == "Hello WORLD Test"

    def test_normalize_multiple_punctuation(self):
        """Reduce repeated punctuation."""
        preprocessor = TextCleaner()
        document = {"content": "Hello!!! World??? Test..."}

        result = preprocessor.process(document)

        assert result["content"] == "Hello! World? Test."

    def test_metadata_preserved(self):
        """Metadata should be preserved through processing."""
        preprocessor = TextCleaner()
        document = {
            "content": "Hello!!!",
            "metadata": {"filename": "test.txt"}
        }

        result = preprocessor.process(document)

        assert result["metadata"] == {"filename": "test.txt"}
        assert result["content"] == "Hello!"


class TestPreprocessorErrorHandling:
    """Tests for error handling in preprocessors."""

    def test_missing_content_key(self):
        """Handle document without content."""
        preprocessor = WhitespaceNormalizer()
        document = {"metadata": {"filename": "test.txt"}}

        with pytest.raises(PreprocessorError) as exc_info:
            preprocessor.process(document)

        assert "content" in str(exc_info.value).lower()

    def test_preprocessor_chaining(self):
        """Chain multiple preprocessors."""
        doc = {"content": "Hello   \u201cWorld\u201d!!!"}

        # First normalize whitespace
        doc = WhitespaceNormalizer().process(doc)
        assert doc["content"] == 'Hello \u201cWorld\u201d!!!'

        # Then clean text
        doc = TextCleaner(normalize_quotes=True).process(doc)
        # Check that quotes were normalized and punctuation reduced
        assert '"' in doc["content"]
        assert "\u201c" not in doc["content"]
        assert doc["content"].endswith('!')
        assert not doc["content"].endswith('!!!')


class TestPreprocessorEdgeCases:
    """Tests for edge cases in preprocessors."""

    def test_whitespace_normalizer_empty_string(self):
        """Handle empty string input."""
        preprocessor = WhitespaceNormalizer()
        document = {"content": ""}
        
        result = preprocessor.process(document)
        
        assert result["content"] == ""
    
    def test_whitespace_normalizer_only_whitespace(self):
        """Handle document with only whitespace."""
        preprocessor = WhitespaceNormalizer()
        document = {"content": "   \t\t   \n  "}
        
        result = preprocessor.process(document)
        
        # Should normalize to empty or single space
        assert result["content"].strip() == ""
    
    def test_text_cleaner_empty_string(self):
        """Handle empty string input."""
        preprocessor = TextCleaner()
        document = {"content": ""}
        
        result = preprocessor.process(document)
        
        assert result["content"] == ""
    
    def test_text_cleaner_special_characters(self):
        """Handle text with special unicode characters."""
        preprocessor = TextCleaner(normalize_quotes=True)
        document = {"content": "Test with © trademark™ and ® symbols"}
        
        result = preprocessor.process(document)
        
        # Should preserve special characters
        assert "©" in result["content"] or "trademark" in result["content"]
    
    def test_text_cleaner_mixed_punctuation(self):
        """Handle mixed punctuation marks."""
        preprocessor = TextCleaner()
        document = {"content": "What?!?! Really!!!??? Yes..."}
        
        result = preprocessor.process(document)
        
        # Punctuation should be reduced (not completely normalized)
        original_exclamation = document["content"].count("!")
        result_exclamation = result["content"].count("!")
        assert result_exclamation < original_exclamation
