"""Command-line orchestration for explicit connected model installation."""

import argparse
import pathlib
import subprocess

from speech_translate import config
from speech_translate.installation import (
    downloads,
    multilingual,
    speech_models,
)


def parse_arguments(argv=None) -> argparse.Namespace:
    """Parse the optional model size and destination folder."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--speech-model", choices=config.SPEECH_MODELS, default="small"
    )
    parser.add_argument(
        "--models-dir", type=pathlib.Path, default=config.MODELS
    )
    return parser.parse_args(argv)


def record(path: pathlib.Path, key: str, entry: dict) -> None:
    """Preserve earlier manifest entries when recording one installed model."""
    if entry:
        manifest = downloads.read_json(path)
        manifest[key] = entry
        downloads.write_json(path, manifest)


def install_all(models: pathlib.Path, size: str) -> None:
    """Install each model independently so setup can resume after failure."""
    models.mkdir(parents=True, exist_ok=True)
    manifest = models / "manifest.json"
    record(manifest, f"speech/{size}", speech_models.install(models, size))
    print("Preparing multilingual translation…", flush=True)
    record(manifest, "translation/m2m100", multilingual.install(models))


def main(argv=None) -> int:
    """Install local models and report recoverable setup failures."""
    args = parse_arguments(argv)
    try:
        install_all(args.models_dir.resolve(), args.speech_model)
    except (
        config.AppError,
        OSError,
        ValueError,
        RuntimeError,
        subprocess.CalledProcessError,
    ) as error:
        print(f"Model setup failed: {error}\nRun this command again to retry.")
        return 1
    print(f"Models ready in {args.models_dir}. The app can now run offline.")
    return 0
