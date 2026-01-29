"""Registry for postprocessors."""

from scruby.registry import ComponentRegistry

# Create postprocessor registry
postprocessor_registry = ComponentRegistry("postprocessor")


def get_postprocessor_registry() -> ComponentRegistry:
    """Get the global postprocessor registry."""
    return postprocessor_registry
