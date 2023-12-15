from setuptools import setup

setup(
    name="helper-cli",
    version="0.0.1",
    py_modules=["helper_cli"],
    install_requires=[
        "Click",
        "websockets",
        "uvicorn",
        "fastapi",
        "psutil",
        "loguru",
        "pydantic_settings",
        "python-multipart",
        "mnemonic",
    ],
    entry_points={
        "console_scripts": [
            "helper-cli = helper_cli.cli:cli",
        ],
    },
)
