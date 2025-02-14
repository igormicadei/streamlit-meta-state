from typing import Any
from streamlit.runtime.state.common import require_valid_user_key
from streamlit.runtime.state import get_session_state
from streamlit.runtime.state.safe_session_state import SafeSessionState


class SessionVar:
    """A descriptor that stores values in Streamlit's session_state, while also exposing a read-only `key` property."""

    class _Wrapper:
        """A wrapper that enables `.key` storage and type delegation, while making `key` read-only."""

        def __init__(self, value, key, descriptor, instance):
            object.__setattr__(self, "_value", value)
            object.__setattr__(self, "_key", key)  # Read-only key
            object.__setattr__(self, "_descriptor", descriptor)
            object.__setattr__(self, "_instance", instance)

        @property
        def key(self):
            """Read-only access to the session key."""
            return object.__getattribute__(self, "_key")

        def __getattr__(self, item):
            """First check if `self` has the attribute; otherwise, delegate to `_value`."""
            if item in ("_value", "_key", "_descriptor", "_instance"):
                return object.__getattribute__(self, item)
            return getattr(self._value, item)

        def __setattr__(self, name, value):
            """Allow setting attributes while ensuring key updates are stored properly."""
            if name in ("_value", "_key", "_descriptor", "_instance"):
                raise AttributeError(f"Cannot modify attribute '{name}' directly.")
            setattr(self._value, name, value)

        def __str__(self):
            return str(self._value)

        def __repr__(self):
            return repr(self._value)

        def __call__(self, *args, **kwargs):
            """Allow callable values to be called directly."""
            if callable(self._value):
                return self._value(*args, **kwargs)
            raise TypeError(f"'{type(self._value).__name__}' object is not callable")

        def __eq__(self, other):
            """Support equality checks against the stored value."""
            return self._value == other

        def __getitem__(self, item):
            """Support indexing if the stored value is indexable (list, dict, etc.)."""
            return self._value[item]

        def __setitem__(self, key, value):
            """Support item assignment if the stored value is mutable."""
            self._value[key] = value

        def __iter__(self):
            """Support iteration if the stored value is iterable."""
            return iter(self._value)

        def __len__(self):
            """Support len() if the stored value supports it."""
            return len(self._value)

    def __init__(self, name: str) -> None:
        self.name: str = name

    def _make_key(self, instance) -> str:
        return f"{instance.__instance_key__}.{self.name}"

    def __get__(self, instance, owner) -> Any:
        if instance is None:
            return self  # Allow access to the descriptor via the class

        key: str = self._make_key(instance)
        require_valid_user_key(key)
        state: SafeSessionState = get_session_state()

        # Retrieve cached value
        if key in state:
            value = state[key]
        else:
            value = None

        # Store in instance cache with a read-only key
        wrapped = SessionVar._Wrapper(value, key, self, instance)
        instance.__dict__[self.name] = wrapped
        return wrapped

    def __set__(self, instance, value) -> None:
        """Stores a new value while preserving the read-only key."""
        key: str = self._make_key(instance)
        require_valid_user_key(key)
        state: SafeSessionState = get_session_state()

        # Update value and ensure it's wrapped
        wrapped = SessionVar._Wrapper(value, key, self, instance)
        instance.__dict__[self.name] = wrapped
        state[key] = value  # Store only value (key is derived)


class MetaSessionState(type):
    """
    Metaclass that binds class attributes to Streamlit's session state.

    This metaclass automatically replaces annotated attributes with SessionVar descriptors,
    ensuring that the values are stored and retrieved from Streamlit's session state. It also
    manages instance creation by using a unique session key to persist and retrieve instances.
    """

    def __call__(cls, *args, **kwargs):
        """
        Create or retrieve an instance associated with a unique session key.

        This method extracts the 'instance_key' from kwargs, builds a unique instance key, and
        checks whether an instance with that key exists in the session state. If it does, that
        instance is returned; otherwise, a new instance is created, stored in the session state,
        and returned.

        Args:
            *args: Positional arguments for the instance initialization.
            **kwargs: Keyword arguments for the instance initialization. Must include 'instance_key'.

        Returns:
            Any: The instance associated with the given session key.

        Raises:
            KeyError: If 'instance_key' is not provided in kwargs.
        """

        if "instance_key" not in kwargs:
            raise KeyError(
                "Instance must have a key set as 'instance_key' to be used on session_state context"
            )

        instance_key: str = kwargs.pop("instance_key")
        instance_key = f"{cls.__module__}_{cls.__name__}_{instance_key}"

        require_valid_user_key(key=instance_key)
        state: SafeSessionState = get_session_state()

        if instance_key not in state:
            instance = cls.__new__(cls)  # type: ignore   # pylint: disable=E1120
            instance.__instance_key__ = instance_key  # pylint: disable=W0201
            instance.__init__(*args, **kwargs)

            state[instance_key] = instance

        return state[instance_key]

    def __new__(mcs, name, bases, class_dict):
        """
        Create a new class and replace annotated attributes with SessionVar descriptors.

        This method intercepts class creation, finds all attributes defined via annotations, and
        replaces them with SessionVar instances.
        This ensures that those attributes are automatically managed via Streamlit's session state.

        Args:
            name (str): The name of the class.
            bases (tuple): A tuple of base classes.
            class_dict (dict): The class dictionary containing attributes and annotations.

        Returns:
            Self: The newly created class with SessionVar-bound attributes.
        """
        new_class = super().__new__(mcs, name, bases, class_dict)

        for var_name in class_dict.get("__annotations__", {}):
            setattr(new_class, var_name, SessionVar(var_name))

        return new_class
