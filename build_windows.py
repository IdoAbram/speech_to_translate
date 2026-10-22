"""Build a Windows application that includes Python and all offline models."""

import argparse
import pathlib
import shutil
import subprocess
import sys

import build_support
from speech_translate import config
from speech_translate.speech import engine
from speech_translate.translation import packages


def runtime_options() -> list[str]:
    """Collect native inference assets while excluding setup-only libraries."""
    options = ["--windowed", "--noconfirm", "--noupx"]
    for package in (
        "ctranslate2",
        "faster_whisper",
        "tokenizers",
        "sentencepiece",
    ):
        options += ["--collect-all", package]
    for package in ("torch", "transformers", "pytest", "pytestqt", "ruff"):
        options += ["--exclude-module", package]
    return options


def model_assets() -> list[pathlib.Path]:
    """Ship the selected speech model and the single multilingual translator."""
    return [
        engine.model_path(config.MODELS, "small"),
        packages.multilingual_path(config.MODELS),
    ]


def build(single_file: bool) -> pathlib.Path:
    """Freeze an executable, optionally embedding every offline model."""
    assets = model_assets()
    name = "SongWords" if single_file else "SongWordsPortable"
    arguments = [sys.executable, "-m", "PyInstaller", *runtime_options()]
    arguments += build_support.data_options()
    arguments += ["--name", name, "--onefile" if single_file else "--onedir"]
    if single_file:
        for path in assets:
            relative = pathlib.Path("models") / path.relative_to(config.MODELS)
            arguments += ["--add-data", f"{path};{relative}"]
    subprocess.run([*arguments, "app.py"], cwd=config.ROOT, check=True)
    output = config.ROOT / "dist" / name
    if not single_file:
        copy_models(output, assets)
    return output.with_suffix(".exe") if single_file else output


def copy_models(output: pathlib.Path, assets: list[pathlib.Path]) -> None:
    """Make the portable folder independent of the source checkout."""
    for path in assets:
        destination = output / "models" / path.relative_to(config.MODELS)
        shutil.copytree(path, destination, dirs_exist_ok=True)
    shutil.copy2(config.ROOT / "README.md", output / "README.md")
    for name in ("LICENSE", "THIRD_PARTY_NOTICES.md"):
        shutil.copy2(config.ROOT / name, output / name)


def main(argv=None) -> int:
    """Build one self-contained EXE by default, or a faster-starting folder."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--portable", action="store_true")
    args = parser.parse_args(argv)
    if sys.platform != "win32":
        parser.error("Build on Windows to produce a Windows executable.")
    print(f"Ready: {build(not args.portable)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
