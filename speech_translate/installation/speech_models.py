"""Install one pinned revision of the multilingual Whisper model."""

import pathlib

from speech_translate.installation import downloads
from speech_translate.speech import engine

FILES = (
    "config.json",
    "model.bin",
    "tokenizer.json",
    "vocabulary.txt",
    "vocabulary.json",
    "preprocessor_config.json",
    "README.md",
)


def repository_info(path: pathlib.Path, repository: str) -> dict:
    """Pin retries to the same revision, including its file inventory."""
    revision_file = path / ".download-revision"
    url = f"https://huggingface.co/api/models/{repository}"
    if revision_file.exists():
        url += "/revision/" + revision_file.read_text(encoding="utf-8")
    info = downloads.fetch_json(url)
    revision_file.write_text(info["sha"], encoding="utf-8")
    return info


def fetch_files(path: pathlib.Path, repository: str, info: dict) -> None:
    """Download only the model's runtime assets and attribution."""
    available = {entry["rfilename"] for entry in info["siblings"]}
    base = f"https://huggingface.co/{repository}/resolve/{info['sha']}"
    for name in FILES:
        if name in available and not (path / name).exists():
            downloads.download(f"{base}/{name}", path / name)


def install(models: pathlib.Path, size: str) -> dict:
    """Install missing speech files and return their revision provenance."""
    path = models / "speech" / size
    marker = path / ".complete"
    if marker.exists():
        engine.model_path(models, size)
        return {}
    path.mkdir(parents=True, exist_ok=True)
    repository = f"Systran/faster-whisper-{size}"
    info = repository_info(path, repository)
    fetch_files(path, repository, info)
    engine.model_path(models, size)
    marker.write_text(info["sha"], encoding="utf-8")
    return {"repository": repository, "revision": info["sha"]}
