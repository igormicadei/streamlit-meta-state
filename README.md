# StreamlitMetaState

StreamlitMetaState is a Python package that enables seamless session persistence for class instances in [Streamlit](https://streamlit.io) applications. By leveraging a metaclass and descriptors, it automatically binds class attributes to Streamlit's session state, eliminating the need for manual session management.

## Features

- **Automatic Session Persistence**: No need to manually store and retrieve instance data in Streamlit session state.
- **Seamless Integration**: Works with any class by simply using `StreamlitMetaState` as a metaclass.
- **State Synchronization**: Ensures attributes remain synchronized between session state and class instances.
- **Instance Persistence**: Supports multiple instances with unique session keys.

## Installation

Install StreamlitMetaState via pip:

```bash
pip install streamlit-meta-state
```

## Usage

To ensure proper functionality, **class variables must be annotated** in the class definition.

### Simple Use

```python
import streamlit as st
from streamlit_meta_state import MetaSessionState

class MyPersistentClass(metaclass=MetaSessionState):
    name: str
    counter: int

    def __init__(self, name: str, counter: int):
        self.name = name
        self.counter = counter

# Create a persistent instance
my_instance = MyPersistentClass(name="Example", counter=10, instance_key="example_instance")

st.write(f"The counter for '{my_instance.name}' is currently {my_instance.counter}")
if st.button(label=f"Increase '{my_instance.name}'"):
    my_instance.counter += 1  # Changes persist across reruns
    st.rerun()
```

### Widget Binding

You can bind Streamlit widgets directly to class attributes using their session keys:

```python
st.text_input(label="MyPersistentClass.name", key=my_instance.name.key)

st.write(f"The current value on the 'MyPersistentClass.name' is '{my_instance.name}'")
```

## How It Works

1. **SessionVar Descriptor**: Each class attribute is wrapped with a descriptor that synchronizes its value with Streamlit's session state.
2. **MetaSessionState Metaclass**: Replaces annotated attributes with `SessionVar` and ensures instances are stored persistently using a unique `instance_key`.
3. **Automatic State Management**: Attribute changes are automatically reflected in session state without extra handling.

## License

This project is licensed under the MIT License.

## Contributing

Contributions are welcome! If you'd like to improve StreamlitMetaState, feel free to submit a pull request.

## Issues

If you encounter any issues, please open an [issue on GitHub](https://github.com/igormicadei/streamlit-meta-state/issues).

