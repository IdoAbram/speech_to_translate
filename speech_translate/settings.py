"""Per-user preferences that survive restarts and newer executables."""

import json

from speech_translate import config

FILE_NAME = "settings.json"


def load() -> dict:
    """Read saved preferences, treating a missing or broken file as empty."""
    path = config.settings_dir() / FILE_NAME
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return data if isinstance(data, dict) else {}


def save(values: dict) -> None:
    """Merge values into the saved preferences."""
    path = config.settings_dir() / FILE_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    merged = {**load(), **values}
    path.write_text(json.dumps(merged, indent=2), encoding="utf-8")


def online_enabled() -> bool:
    """Return whether translation may use Groq when a key is saved."""
    return load().get("online_translation", True) is not False


def set_online_enabled(enabled: bool) -> None:
    """Turn online translation on or off without forgetting the key."""
    save({"online_translation": bool(enabled)})
