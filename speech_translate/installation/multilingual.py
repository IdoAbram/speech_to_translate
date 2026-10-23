"""Install the official NLLB-200 model and quantize it for offline CPUs."""

import pathlib
import shutil

from speech_translate import config
from speech_translate.installation import conversion, downloads, speech_models
from speech_translate.translation import packages

# Distilled 600M: clearly better than M2M100 418M at a similar CPU cost.
REPOSITORY = "facebook/nllb-200-distilled-600M"
FILES = (
    "config.json",
    "generation_config.json",
    "pytorch_model.bin",
    "sentencepiece.bpe.model",
    "tokenizer.json",
    "tokenizer_config.json",
    "special_tokens_map.json",
    "README.md",
)


def fetch_source(path: pathlib.Path) -> dict:
    """Download the original model with a revision pinned across retries."""
    path.mkdir(parents=True, exist_ok=True)
    info = speech_models.repository_info(path, REPOSITORY)
    available = {item["rfilename"] for item in info["siblings"]}
    base = f"https://huggingface.co/{REPOSITORY}/resolve/{info['sha']}"
    for name in FILES:
        if name in available and not (path / name).exists():
            downloads.download(f"{base}/{name}", path / name)
    return info


def install(models: pathlib.Path) -> dict:
    """Reuse completed weights or finish a resumable local conversion."""
    destination = models / "translation" / "nllb"
    marker = destination / ".complete"
    if marker.exists():
        packages.multilingual_path(models)
        return {}
    source = config.ROOT / ".downloads" / "nllb-source"
    info = fetch_source(source)
    destination.mkdir(parents=True, exist_ok=True)
    conversion.convert(source, destination / "model")
    for name in ("sentencepiece.bpe.model", "README.md"):
        shutil.copy2(source / name, destination / name)
    packages.multilingual_path(models)
    marker.write_text(info["sha"], encoding="utf-8")
    return {
        "repository": REPOSITORY,
        "revision": info["sha"],
        "quantization": "int8",
    }
