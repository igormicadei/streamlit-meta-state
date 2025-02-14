"""
Module for managing Streamlit session state using descriptors and a metaclass.

This module provides a mechanism to automatically bind class attributes (defined via
type annotations) to Streamlit's session state. It leverages the `SessionVar` descriptor to
synchronize attribute values with the session state and the `MetaSessionState` metaclass to
ensure that instances are uniquely stored and retrieved based on a session key.
"""

from typing import Any

from streamlit.runtime.state.common import require_valid_user_key
from streamlit.runtime.state import get_session_state
from streamlit.runtime.state.safe_session_state import SafeSessionState


class SessionVar:
    """
    Descriptor to store and retrieve attribute values in Streamlit's session state.

    This descriptor synchronizes an attribute with Streamlit's session state. It maintains
    a local cache on the instance (using the instance's __dict__) to avoid repeated lookups
    and to ensure consistency between the in-memory value and the session state value.
    """

    def __init__(self, name: str) -> None:
        """
        Initialize the SessionVar descriptor.

        Args:
            name (str): The name of the attribute to be managed.
        """
        self.name: str = name

        # Store the session state key for this attribute, generated when
        # `_make_key` is called.
        self._key: str | None = None

    @property
    def cache_name(self) -> str:
        """
        Get the cache name used for storing the attribute in the instance's __dict__.

        Returns:
            str: The cache name, which is the attribute name prefixed with an underscore.
        """
        return f"_{self.name}"
    
    @property
    def key(self) -> str:
        """
        Get the session state key for this attribute.

        Returns:
            str: The session state key in the format '<instance_key>.<attribute_name>'.
        """
        if self._key is None:
            raise ValueError("SessionVar key not set")
        return self._key

    def _make_key(self, instance) -> str:
        """
        Construct a unique session state key for this attribute in the given instance.

        Args:
            instance: The instance of the class containing the attribute.

        Returns:
            str: A unique key in the format '<instance_key>.<attribute_name>'.
        """
        self._key = f"{instance.__instance_key__}.{self.name}"
        return self._key

    def __get__(self, instance, owner) -> Any:
        """
        Retrieve the attribute value from Streamlit's session state.

        If the session state does not contain the key for this attribute, it is initialized
        with the cached value from the instance. If the session state value differs from the
        instance's cached value, the cache is updated accordingly.

        Args:
            instance: The instance from which to retrieve the attribute.
            owner: The owner class.

        Returns:
            Any: The value stored in the session state for this attribute.
        """
        key: str = self._make_key(instance=instance)
        require_valid_user_key(key=key)
        state: SafeSessionState = get_session_state()
        cached: Any = instance.__dict__.get(self.cache_name)

        if key not in state:
            state[key] = cached
        elif state[key] != cached:
            instance.__dict__[self.cache_name] = state[key]

        return state[key]

    def __set__(self, instance, value) -> None:
        """
        Set the attribute value in both the instance's cache and Streamlit's session state.

        Args:
            instance: The instance whose attribute is to be set.
            value: The new value for the attribute.
        """

        key: str = self._make_key(instance=instance)
        instance.__dict__[self.cache_name] = value
        require_valid_user_key(key=key)
        get_session_state()[key] = value


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
