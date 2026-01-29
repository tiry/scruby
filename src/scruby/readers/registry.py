"""Registry for reader components."""

from scruby.registry import ComponentRegistry

# Create the reader registry instance
reader_registry = ComponentRegistry("reader")


def get_reader_registry() -> ComponentRegistry:
    """Get the reader registry instance."""
    return reader_registry
