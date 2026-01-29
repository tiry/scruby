"""Generic registry and factory pattern for pluggable components."""

from typing import Any, Callable, Dict, List, Type


class RegistrationError(Exception):
    """Raised when component registration fails."""

    pass


class ComponentRegistry:
    """
    Generic registry for pluggable components.

    Provides registration, retrieval, and factory methods for components.
    Thread-safe for concurrent access.
    """

    def __init__(self, component_type: str) -> None:
        """
        Initialize the registry.

        Args:
            component_type: Human-readable name for the component type
                          (e.g., "reader", "writer", "redactor")
        """
        self._component_type = component_type
        self._registry: Dict[str, Type] = {}

    def register(
        self, name: str, component_class: Type, override: bool = False
    ) -> None:
        """
        Register a component class.

        Args:
            name: Unique name for the component
            component_class: The class to register
            override: If True, allow overriding existing registrations

        Raises:
            RegistrationError: If name already registered and override=False
        """
        if name in self._registry and not override:
            raise RegistrationError(
                f"{self._component_type} '{name}' is already registered"
            )

        self._registry[name] = component_class

    def register_decorator(self, name: str) -> Callable:
        """
        Decorator for registering component classes.

        Args:
            name: Unique name for the component

        Returns:
            Decorator function

        Example:
            @registry.register_decorator("my_component")
            class MyComponent:
                pass
        """

        def decorator(cls: Type) -> Type:
            self.register(name, cls)
            return cls

        return decorator

    def get(self, name: str) -> Type:
        """
        Get a registered component class.

        Args:
            name: Name of the component

        Returns:
            The registered component class

        Raises:
            RegistrationError: If component not found
        """
        if name not in self._registry:
            available = ", ".join(self.list_available()) or "none"
            raise RegistrationError(
                f"{self._component_type} '{name}' not found. "
                f"Available: {available}"
            )

        return self._registry[name]

    def is_registered(self, name: str) -> bool:
        """
        Check if a component is registered.

        Args:
            name: Name of the component

        Returns:
            True if registered, False otherwise
        """
        return name in self._registry

    def list_available(self) -> List[str]:
        """
        List all registered component names.

        Returns:
            Sorted list of registered component names
        """
        return sorted(self._registry.keys())

    def create(self, component_name: str, **kwargs: Any) -> Any:
        """
        Factory method: create instance of registered component.

        Args:
            component_name: Name of the component to instantiate
            **kwargs: Arguments to pass to component constructor

        Returns:
            Instance of the component

        Raises:
            RegistrationError: If component not found
            TypeError: If component cannot be instantiated with given args
        """
        component_class = self.get(component_name)

        try:
            return component_class(**kwargs)
        except TypeError as e:
            raise TypeError(
                f"Failed to instantiate {self._component_type} '{component_name}': {e}"
            ) from e

    def unregister(self, name: str) -> None:
        """
        Unregister a component (useful for testing).

        Args:
            name: Name of the component to unregister

        Raises:
            RegistrationError: If component not found
        """
        if name not in self._registry:
            raise RegistrationError(
                f"{self._component_type} '{name}' not registered"
            )

        del self._registry[name]

    def clear(self) -> None:
        """Clear all registrations (useful for testing)."""
        self._registry.clear()
