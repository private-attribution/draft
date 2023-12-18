from setuptools import setup

setup(
    name="draft",
    version="0.0.1",
    py_modules=["draft"],
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
        "pyre-check",
    ],
    entry_points={
        "console_scripts": [
            "draft = sidecar.cli.cli:cli",
        ],
    },
)
