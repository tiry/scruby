"""Whitespace normalization preprocessor."""

import re
from typing import Any, Dict

from .base import Preprocessor, PreprocessorError
from .registry import preprocessor_registry


@preprocessor_registry.register_decorator("whitespace_normalizer")
class WhitespaceNormalizer(Preprocessor):
    """
    Normalizes whitespace in documents.

    - Converts tabs to spaces
    - Converts multiple spaces to single space
    - Removes leading/trailing whitespace from lines
    - Normalizes line breaks to \n
    """

    def __init__(self, preserve_paragraphs: bool = True):
        """
        Initialize the whitespace normalizer.

        Args:
            preserve_paragraphs: If True, preserve paragraph breaks (double newlines)
        """
        self.preserve_paragraphs = preserve_paragraphs

    def process(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Normalize whitespace in document.

        Args:
            document: Document with 'content' key

        Returns:
            Document with normalized content

        Raises:
            PreprocessorError: If processing fails
        """
        if "content" not in document:
            raise PreprocessorError("Document must contain 'content' key")

        try:
            content = document["content"]

            # Convert tabs to spaces
            content = content.replace("\t", " ")

            # Normalize line breaks
            content = content.replace("\r\n", "\n").replace("\r", "\n")

            if self.preserve_paragraphs:
                # Preserve double newlines (paragraph breaks)
                # Replace 2+ newlines with placeholder
                content = re.sub(r"\n\n+", "<<<PARAGRAPH>>>", content)
                # Remove multiple spaces
                content = re.sub(r" +", " ", content)
                # Restore paragraph breaks
                content = content.replace("<<<PARAGRAPH>>>", "\n\n")
            else:
                # Replace all whitespace sequences with single space
                content = re.sub(r"\s+", " ", content)

            # Strip leading/trailing whitespace
            content = content.strip()

            # Return modified document
            return {**document, "content": content}
        except Exception as e:
            raise PreprocessorError(f"Failed to normalize whitespace: {e}") from e
