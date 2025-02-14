import streamlit as st
from src.streamlit_meta_state import MetaSessionState


class MyPersistentClass(metaclass=MetaSessionState):
    name: str
    counter: int

    def __init__(self, name: str, counter: int):
        self.name = name
        self.counter = counter


# Create a persistent instance
my_instance = MyPersistentClass(
    name="Example", counter=10, instance_key="example_instance"
)

st.write(f"The counter for '{my_instance.name}' is currently {my_instance.counter}")
if st.button(label=f"Increase '{my_instance.name}'"):
    my_instance.counter += 1  # Changes persist across reruns
    st.rerun()

st.text_input(
    label="MyPersistentClass.name", key=my_instance.name.key
)

st.write(f"The current value on the 'MyPersistentClass.name' is '{my_instance.name}'")
