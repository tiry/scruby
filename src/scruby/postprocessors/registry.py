"""Registry for postprocessors."""

from scruby.registry import ComponentRegistry

# Create postprocessor registry
_postprocessor_registry = ComponentRegistry("postprocessor")


def get_postprocessor_registry() -> ComponentRegistry:
    """Get the global postprocessor registry."""
    return _postprocessor_registry
