"""Shared paths, language choices, errors, and operation callbacks."""

import dataclasses
import os
import pathlib
import sys
import threading
from collections.abc import Callable

ROOT = (
    pathlib.Path(sys.executable).resolve().parent
    if getattr(sys, "frozen", False)
    else pathlib.Path(__file__).resolve().parent.parent
)
MODELS = ROOT / "models"
if not MODELS.is_dir() and getattr(sys, "frozen", False):
    MODELS = pathlib.Path(sys._MEIPASS) / "models"
LANGUAGES = {"en": "English", "he": "Hebrew", "pl": "Polish"}
SPEECH_MODELS = ("base", "small", "medium")
THREADS = max(1, min(4, (os.cpu_count() or 2) - 1))
Progress = Callable[[str, int], None]


class AppError(Exception):
    """An actionable error suitable for displaying in the UI."""


class Cancelled(AppError):
    """An operation stopped at the user's request."""


def ignore_progress(message: str, percent: int) -> None:
    """Accept progress updates when no listener was supplied."""


def ignore_notice(message: str) -> None:
    """Accept result notices when no listener was supplied."""


def settings_dir() -> pathlib.Path:
    """Per-user settings that survive replacing or moving the executable."""
    base = os.environ.get("APPDATA") or str(pathlib.Path.home())
    return pathlib.Path(base) / "SongWords"


def validate_language(code: str) -> None:
    """Raise AppError for a language outside the supported set."""
    if code not in LANGUAGES:
        raise AppError("Choose English, Hebrew, or Polish.")


def offline_mode() -> None:
    """Disable model downloads and telemetry before inference imports."""
    os.environ["HF_HUB_OFFLINE"] = "1"
    os.environ["HF_HUB_DISABLE_TELEMETRY"] = "1"
    os.environ["TRANSFORMERS_OFFLINE"] = "1"


@dataclasses.dataclass
class Operation:
    """Progress, cooperative cancellation, and notices for one operation.

    A notice describes how the result was produced, such as a fallback to
    the offline model, and stays visible after the operation finishes.
    """

    progress: Progress = ignore_progress
    cancel: threading.Event | None = None
    notice: Callable[[str], None] = ignore_notice

    def check(self) -> None:
        """Raise Cancelled if cancellation was requested."""
        if self.cancel is not None and self.cancel.is_set():
            raise Cancelled("Cancelled. Your completed transcript is kept.")

    def report(self, message: str, percent: int = -1) -> None:
        """Check cancellation and report progress; -1 means indeterminate."""
        self.check()
        self.progress(message, percent)
