"""Tests for the registry and factory pattern."""

import pytest

from scruby.registry import ComponentRegistry, RegistrationError


# Test fixture components
class DummyComponent:
    """Component with no constructor args."""

    pass


class ComponentWithArgs:
    """Component with positional args."""

    def __init__(self, value: int):
        self.value = value


class ComponentWithKwargs:
    """Component with keyword args."""

    def __init__(self, name: str, count: int = 0):
        self.name = name
        self.count = count


class ComponentWithComplexInit:
    """Component with complex initialization."""

    def __init__(self, config: dict, *args, **kwargs):
        self.config = config
        self.args = args
        self.kwargs = kwargs


class TestRegistryInitialization:
    """Tests for registry initialization."""

    def test_registry_initialization(self):
        """Create registry with component type, verify empty registry."""
        registry = ComponentRegistry("test_component")
        assert registry._component_type == "test_component"
        assert registry.list_available() == []


class TestComponentRegistration:
    """Tests for component registration."""

    def test_register_component(self):
        """Register a component class, verify it's stored correctly."""
        registry = ComponentRegistry("test")
        registry.register("dummy", DummyComponent)

        assert registry.is_registered("dummy")
        assert registry.get("dummy") == DummyComponent

    def test_register_duplicate_without_override(self):
        """Register same name twice without override, verify error is raised."""
        registry = ComponentRegistry("test")
        registry.register("dummy", DummyComponent)

        with pytest.raises(RegistrationError) as exc_info:
            registry.register("dummy", ComponentWithArgs)

        assert "already registered" in str(exc_info.value)
        assert "dummy" in str(exc_info.value)

    def test_register_duplicate_with_override(self):
        """Register same name twice with override=True, verify replacement."""
        registry = ComponentRegistry("test")
        registry.register("dummy", DummyComponent)
        registry.register("dummy", ComponentWithArgs, override=True)

        # Should be the second class now
        assert registry.get("dummy") == ComponentWithArgs

    def test_register_decorator(self):
        """Use decorator to register component, verify registration."""
        registry = ComponentRegistry("test")

        @registry.register_decorator("decorated")
        class DecoratedComponent:
            pass

        # Verify component is registered
        assert registry.is_registered("decorated")
        assert registry.get("decorated") == DecoratedComponent

        # Verify decorator returns original class
        assert DecoratedComponent.__name__ == "DecoratedComponent"


class TestComponentRetrieval:
    """Tests for component retrieval."""

    def test_get_registered_component(self):
        """Register and retrieve component, verify correct class returned."""
        registry = ComponentRegistry("test")
        registry.register("dummy", DummyComponent)

        component_class = registry.get("dummy")
        assert component_class == DummyComponent

    def test_get_unregistered_component(self):
        """Try to get non-existent component, verify error."""
        registry = ComponentRegistry("test")

        with pytest.raises(RegistrationError) as exc_info:
            registry.get("nonexistent")

        error_msg = str(exc_info.value)
        assert "nonexistent" in error_msg
        assert "not found" in error_msg
        assert "Available: none" in error_msg

    def test_get_unregistered_with_available_components(self):
        """Try to get non-existent component when others exist."""
        registry = ComponentRegistry("test")
        registry.register("comp1", DummyComponent)
        registry.register("comp2", ComponentWithArgs)

        with pytest.raises(RegistrationError) as exc_info:
            registry.get("nonexistent")

        error_msg = str(exc_info.value)
        assert "Available: comp1, comp2" in error_msg

    def test_is_registered(self):
        """Check registered and unregistered components."""
        registry = ComponentRegistry("test")
        registry.register("dummy", DummyComponent)

        assert registry.is_registered("dummy") is True
        assert registry.is_registered("nonexistent") is False


class TestComponentListing:
    """Tests for listing available components."""

    def test_list_available(self):
        """Register multiple components, verify list is sorted and complete."""
        registry = ComponentRegistry("test")
        registry.register("zebra", DummyComponent)
        registry.register("apple", ComponentWithArgs)
        registry.register("banana", ComponentWithKwargs)

        available = registry.list_available()
        assert available == ["apple", "banana", "zebra"]

    def test_list_available_empty(self):
        """List components in empty registry, verify empty list."""
        registry = ComponentRegistry("test")
        assert registry.list_available() == []


class TestComponentFactory:
    """Tests for factory method (component instantiation)."""

    def test_create_component_no_args(self):
        """Create component that takes no args, verify instance created."""
        registry = ComponentRegistry("test")
        registry.register("dummy", DummyComponent)

        instance = registry.create("dummy")
        assert isinstance(instance, DummyComponent)

    def test_create_component_with_args(self):
        """Create component with constructor args, verify args passed."""
        registry = ComponentRegistry("test")
        registry.register("with_args", ComponentWithArgs)

        instance = registry.create("with_args", value=42)
        assert isinstance(instance, ComponentWithArgs)
        assert instance.value == 42

    def test_create_component_with_kwargs(self):
        """Create component with keyword args, verify kwargs passed."""
        registry = ComponentRegistry("test")
        registry.register("with_kwargs", ComponentWithKwargs)

        instance = registry.create("with_kwargs", name="test", count=5)
        assert isinstance(instance, ComponentWithKwargs)
        assert instance.name == "test"
        assert instance.count == 5

    def test_create_component_with_default_kwargs(self):
        """Create component using default kwargs."""
        registry = ComponentRegistry("test")
        registry.register("with_kwargs", ComponentWithKwargs)

        instance = registry.create("with_kwargs", name="test")
        assert isinstance(instance, ComponentWithKwargs)
        assert instance.name == "test"
        assert instance.count == 0  # Default value

    def test_create_unregistered_component(self):
        """Try to create non-existent component, verify error."""
        registry = ComponentRegistry("test")

        with pytest.raises(RegistrationError) as exc_info:
            registry.create("nonexistent")

        assert "not found" in str(exc_info.value)

    def test_create_component_invalid_args(self):
        """Try to create component with wrong args, verify TypeError."""
        registry = ComponentRegistry("test")
        registry.register("with_args", ComponentWithArgs)

        with pytest.raises(TypeError) as exc_info:
            # Missing required 'value' argument
            registry.create("with_args")

        error_msg = str(exc_info.value)
        assert "Failed to instantiate" in error_msg
        assert "with_args" in error_msg

    def test_create_component_complex_init(self):
        """Create component with complex initialization."""
        registry = ComponentRegistry("test")
        registry.register("complex", ComponentWithComplexInit)

        config = {"key": "value"}
        instance = registry.create("complex", config=config, extra="data")

        assert isinstance(instance, ComponentWithComplexInit)
        assert instance.config == config
        assert instance.kwargs == {"extra": "data"}


class TestComponentUnregistration:
    """Tests for unregistering components."""

    def test_unregister_component(self):
        """Register and unregister component, verify removal."""
        registry = ComponentRegistry("test")
        registry.register("dummy", DummyComponent)

        assert registry.is_registered("dummy")

        registry.unregister("dummy")

        assert not registry.is_registered("dummy")
        assert "dummy" not in registry.list_available()

    def test_unregister_nonexistent(self):
        """Try to unregister non-existent component, verify error."""
        registry = ComponentRegistry("test")

        with pytest.raises(RegistrationError) as exc_info:
            registry.unregister("nonexistent")

        assert "not registered" in str(exc_info.value)
        assert "nonexistent" in str(exc_info.value)


class TestRegistryClear:
    """Tests for clearing the registry."""

    def test_clear_registry(self):
        """Register multiple components, clear registry, verify all removed."""
        registry = ComponentRegistry("test")
        registry.register("comp1", DummyComponent)
        registry.register("comp2", ComponentWithArgs)
        registry.register("comp3", ComponentWithKwargs)

        assert len(registry.list_available()) == 3

        registry.clear()

        assert len(registry.list_available()) == 0
        assert not registry.is_registered("comp1")
        assert not registry.is_registered("comp2")
        assert not registry.is_registered("comp3")


class TestMultipleRegistries:
    """Tests for multiple independent registries."""

    def test_multiple_registries_independent(self):
        """Create two separate registries, verify they don't interfere."""
        registry1 = ComponentRegistry("type1")
        registry2 = ComponentRegistry("type2")

        # Register different components in each
        registry1.register("comp1", DummyComponent)
        registry2.register("comp2", ComponentWithArgs)

        # Verify independence
        assert registry1.is_registered("comp1")
        assert not registry1.is_registered("comp2")

        assert registry2.is_registered("comp2")
        assert not registry2.is_registered("comp1")

        # Verify separate lists
        assert registry1.list_available() == ["comp1"]
        assert registry2.list_available() == ["comp2"]
