# Step 2: Registry & Factory Pattern

**Status**: ✅ Complete  
**Related Spec**: `specs/00-implementation-plan.md`

---

## Goals

1. Create a base registry system for component management
2. Implement factory pattern for component instantiation
3. Provide foundation for all pluggable components (readers, writers, preprocessors, postprocessors, redactors)
4. Implement comprehensive unit tests

---

## Architecture Overview

The registry and factory pattern provides the foundation for scruby's pluggable architecture. Each component type (reader, writer, etc.) will have its own registry to discover and instantiate implementations.

### Key Components

1. **Registry**: Maps component names to their classes
2. **Factory**: Creates instances of registered components
3. **Base Classes**: Abstract interfaces for each component type

---

## Implementation Details

### Registry Pattern

Each component type will have a registry that:
- Maintains a dictionary mapping names to implementation classes
- Provides registration decorator for easy component registration
- Allows retrieval of registered components
- Raises clear errors for unregistered components

### Factory Pattern

The factory will:
- Accept a component name and optional configuration
- Look up the implementation class in the registry
- Instantiate the component with provided configuration
- Return the instantiated component

### Generic Implementation

We'll create a generic `ComponentRegistry` class that can be instantiated for different component types:

```python
class ComponentRegistry:
    """Generic registry for pluggable components."""
    
    def __init__(self, component_type: str):
        self._component_type = component_type
        self._registry: Dict[str, Type] = {}
    
    def register(self, name: str, component_class: Type) -> None:
        """Register a component class."""
        pass
    
    def get(self, name: str) -> Type:
        """Get a registered component class."""
        pass
    
    def list_available(self) -> List[str]:
        """List all registered component names."""
        pass
    
    def create(self, name: str, **kwargs) -> Any:
        """Factory method: create instance of registered component."""
        pass
```

---

## File Structure

```
src/scruby/
├── registry.py          # Generic registry implementation
└── <component_type>/
    ├── base.py         # Abstract base class
    ├── registry.py     # Component-specific registry instance
    └── <impl>.py       # Concrete implementations
```

---

## registry.py Module

### Classes

**ComponentRegistry**
- Generic registry for any component type
- Thread-safe registration and retrieval
- Factory method for instantiation

**RegistrationError**
- Custom exception for registration issues

### API Design

```python
"""Generic registry and factory pattern for pluggable components."""

from typing import Any, Dict, List, Type, Optional, Callable
from abc import ABC


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
        self, 
        name: str, 
        component_class: Type,
        override: bool = False
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
    
    def create(self, name: str, **kwargs: Any) -> Any:
        """
        Factory method: create instance of registered component.
        
        Args:
            name: Name of the component to instantiate
            **kwargs: Arguments to pass to component constructor
            
        Returns:
            Instance of the component
            
        Raises:
            RegistrationError: If component not found
            TypeError: If component cannot be instantiated with given args
        """
        component_class = self.get(name)
        
        try:
            return component_class(**kwargs)
        except TypeError as e:
            raise TypeError(
                f"Failed to instantiate {self._component_type} '{name}': {e}"
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
```

---

## Unit Tests

### Test Coverage (`tests/test_registry.py`)

1. **test_registry_initialization**
   - Create registry with component type
   - Verify empty registry

2. **test_register_component**
   - Register a component class
   - Verify it's stored correctly

3. **test_register_duplicate_without_override**
   - Register same name twice without override
   - Verify RegistrationError is raised

4. **test_register_duplicate_with_override**
   - Register same name twice with override=True
   - Verify second registration replaces first

5. **test_register_decorator**
   - Use decorator to register component
   - Verify component is registered
   - Verify decorator returns original class

6. **test_get_registered_component**
   - Register and retrieve component
   - Verify correct class is returned

7. **test_get_unregistered_component**
   - Try to get non-existent component
   - Verify RegistrationError with helpful message

8. **test_is_registered**
   - Check registered and unregistered components
   - Verify correct boolean results

9. **test_list_available**
   - Register multiple components
   - Verify list is sorted and complete

10. **test_list_available_empty**
    - List components in empty registry
    - Verify empty list

11. **test_create_component_no_args**
    - Create component that takes no args
    - Verify instance is created correctly

12. **test_create_component_with_args**
    - Create component with constructor args
    - Verify args are passed correctly

13. **test_create_component_with_kwargs**
    - Create component with keyword args
    - Verify kwargs are passed correctly

14. **test_create_unregistered_component**
    - Try to create non-existent component
    - Verify RegistrationError

15. **test_create_component_invalid_args**
    - Try to create component with wrong args
    - Verify TypeError with clear message

16. **test_unregister_component**
    - Register and unregister component
    - Verify component is removed

17. **test_unregister_nonexistent**
    - Try to unregister non-existent component
    - Verify RegistrationError

18. **test_clear_registry**
    - Register multiple components
    - Clear registry
    - Verify all components removed

19. **test_multiple_registries_independent**
    - Create two separate registries
    - Verify they don't interfere with each other

---

## Test Fixtures

```python
# Simple test components
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
```

---

## Usage Examples

### Basic Registration

```python
from scruby.registry import ComponentRegistry

# Create a registry for readers
reader_registry = ComponentRegistry("reader")

# Register a component
reader_registry.register("text_file", TextFileReader)

# Or use decorator
@reader_registry.register_decorator("json_file")
class JsonFileReader:
    pass
```

### Factory Usage

```python
# Create an instance
reader = reader_registry.create("text_file", path="/data/input.txt")

# Check if component exists
if reader_registry.is_registered("text_file"):
    reader = reader_registry.create("text_file")
```

### List Available Components

```python
# Get all available readers
available = reader_registry.list_available()
print(f"Available readers: {', '.join(available)}")
```

---

## Success Criteria

- ✅ `registry.py` module implemented with type hints
- ✅ `ComponentRegistry` class with all methods
- ✅ `RegistrationError` exception defined
- ✅ All 19 unit tests pass
- ✅ Test coverage >95% for `registry.py`
- ✅ Clear error messages for all failure cases
- ✅ Thread-safe implementation (for future concurrent use)
- ✅ Decorator registration works correctly

---

## Next Step

After completing Step 2, proceed to:
**Step 3: Reader Components** (`specs/03-reader-components.md`)
