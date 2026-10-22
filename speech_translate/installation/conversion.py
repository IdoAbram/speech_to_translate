"""Isolated, setup-only dependencies for quantizing translation weights."""

import os
import pathlib
import subprocess
import sys

from speech_translate import config


def python_path() -> pathlib.Path:
    """Keep PyTorch and Transformers out of the desktop runtime environment."""
    folder = config.ROOT / ".model-venv"
    executable = folder / (
        "Scripts/python.exe" if os.name == "nt" else "bin/python"
    )
    if not executable.exists():
        subprocess.run([sys.executable, "-m", "venv", str(folder)], check=True)
    return executable


def prepare() -> pathlib.Path:
    """Install the tested converter dependencies in a project-local venv."""
    executable = python_path()
    subprocess.run(
        [
            str(executable),
            "-m",
            "pip",
            "install",
            "-r",
            str(config.ROOT / "requirements-models.txt"),
        ],
        check=True,
    )
    return executable


def convert(source: pathlib.Path, destination: pathlib.Path) -> None:
    """Convert trusted local weights to an INT8 CTranslate2 model."""
    executable = prepare()
    converter = executable.with_name(
        "ct2-transformers-converter.exe"
        if os.name == "nt"
        else "ct2-transformers-converter"
    )
    environment = dict(os.environ, HF_HUB_OFFLINE="1")
    arguments = [str(converter), "--model", str(source)]
    arguments += ["--output_dir", str(destination), "--quantization", "int8"]
    subprocess.run(
        [*arguments, "--force"],
        env=environment,
        check=True,
    )
