from setuptools import setup, find_packages

setup(
    name="StreamlitSessionState",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "streamlit==1.42.0",  # Add your package dependency here
    ],
    test_suite="tests",
    author="Igor Micadei",
    author_email="i.micadei@gmail.com",
    description="A Streamlit module for session state management",
    long_description=open(file="README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/igormicadei/streamlit-session-state",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
