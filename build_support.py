"""Collect dependency notices for both Windows distribution formats."""

import importlib.metadata
import pathlib
import shutil

from speech_translate import config


def collect_licenses() -> pathlib.Path:
    """Retain license and notice files shipped by installed dependencies."""
    destination = config.ROOT / "build" / "licenses"
    destination.mkdir(parents=True, exist_ok=True)
    for line in (
        (config.ROOT / "requirements.lock.txt").read_text().splitlines()
    ):
        if line.strip() and not line.startswith("#"):
            copy_distribution(line.split("==")[0], destination)
    shutil.copytree(config.ROOT / "licenses", destination, dirs_exist_ok=True)
    return destination


def copy_distribution(name: str, destination: pathlib.Path) -> None:
    """Copy package notices into namespaced folders without path traversal."""
    distribution = importlib.metadata.distribution(name)
    for item in distribution.files or ():
        if any(
            word in str(item).lower()
            for word in ("license", "notice", "copying")
        ):
            source = pathlib.Path(distribution.locate_file(item))
            if source.is_file():
                parts = [part for part in item.parts if part not in ("..", ".")]
                target = destination / name / pathlib.Path(*parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source, target)


def data_options() -> list[str]:
    """Embed documentation and dependency licenses in every build."""
    options = ["--add-data", f"{collect_licenses()};licenses"]
    for name in ("LICENSE", "README.md", "THIRD_PARTY_NOTICES.md"):
        options += ["--add-data", f"{config.ROOT / name};."]
    return options
