from setuptools import setup

setup(
    name="helper-cli",
    version="0.0.1",
    py_modules=["helper_cli"],
    install_requires=[
        "Click",
    ],
    entry_points={
        "console_scripts": [
            "helper-cli = helper_cli.cli:cli",
        ],
    },
)
