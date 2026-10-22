"""Shared settings and cancellation behavior."""

import os
import threading

import pytest

from speech_translate import config


@pytest.mark.parametrize("language", ["en", "he", "pl"])
def test_supported_languages(language):
    """Accept all three public language codes."""
    config.validate_language(language)


def test_unsupported_language():
    """Reject unsupported input before a model is loaded."""
    with pytest.raises(config.AppError):
        config.validate_language("fr")


def test_progress_and_cancellation():
    """Cancellation suppresses subsequent progress callbacks."""
    updates = []
    event = threading.Event()
    operation = config.Operation(lambda *args: updates.append(args), event)
    operation.report("Working", 20)
    event.set()
    with pytest.raises(config.Cancelled):
        operation.report("Should not appear", 40)
    assert updates == [("Working", 20)]


def test_offline_environment(monkeypatch):
    """Disable telemetry and downloads even if previously enabled."""
    monkeypatch.setenv("HF_HUB_OFFLINE", "0")
    config.offline_mode()
    config.Operation().report("Ignored")
    assert os.environ["HF_HUB_OFFLINE"] == "1"
    assert os.environ["HF_HUB_DISABLE_TELEMETRY"] == "1"
    assert os.environ["TRANSFORMERS_OFFLINE"] == "1"
