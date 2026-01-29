"""Registry for preprocessor components."""

from scruby.registry import ComponentRegistry

# Create the preprocessor registry instance
preprocessor_registry = ComponentRegistry("preprocessor")


def get_preprocessor_registry() -> ComponentRegistry:
    """Get the preprocessor registry instance."""
    return preprocessor_registry
