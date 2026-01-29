"""Registry for writer components."""

from scruby.registry import ComponentRegistry

# Create the writer registry instance
writer_registry = ComponentRegistry("writer")


def get_writer_registry() -> ComponentRegistry:
    """Get the writer registry instance."""
    return writer_registry
