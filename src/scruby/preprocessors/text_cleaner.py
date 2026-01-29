"""Text cleaning preprocessor."""

import re
from typing import Any, Dict

from .base import Preprocessor, PreprocessorError
from .registry import preprocessor_registry


@preprocessor_registry.register_decorator("text_cleaner")
class TextCleaner(Preprocessor):
    """
    Cleans and normalizes text content.

    - Removes control characters
    - Normalizes quotes
    - Optionally converts to lowercase
    - Removes multiple punctuation
    """

    def __init__(self, lowercase: bool = False, normalize_quotes: bool = True):
        """
        Initialize the text cleaner.

        Args:
            lowercase: If True, convert text to lowercase
            normalize_quotes: If True, normalize curly quotes to straight quotes
        """
        self.lowercase = lowercase
        self.normalize_quotes = normalize_quotes

    def process(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Clean text in document.

        Args:
            document: Document with 'content' key

        Returns:
            Document with cleaned content

        Raises:
            PreprocessorError: If processing fails
        """
        if "content" not in document:
            raise PreprocessorError("Document must contain 'content' key")

        try:
            content = document["content"]

            # Remove control characters (except newlines and tabs)
            content = re.sub(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]", "", content)

            if self.normalize_quotes:
                # Normalize curly quotes to straight quotes
                content = content.replace("\u201c", '"').replace("\u201d", '"')
                content = content.replace("\u2018", "'").replace("\u2019", "'")

            if self.lowercase:
                content = content.lower()

            # Remove multiple punctuation (e.g., "!!!" -> "!")
            content = re.sub(r"([!?.])\1+", r"\1", content)

            # Return modified document
            return {**document, "content": content}
        except Exception as e:
            raise PreprocessorError(f"Failed to clean text: {e}") from e
