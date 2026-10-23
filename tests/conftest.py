"""Offline, deterministic defaults and isolated Qt window fixtures."""

import os
import socket

import pytest
from PySide6 import QtCore

from speech_translate.gui import window
from speech_translate.translation import groq
from tests import helpers

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def deny_network(*args, **kwargs):
    """Fail immediately if any test or inference code attempts networking."""
    raise AssertionError("Network access is forbidden during tests")


@pytest.fixture(autouse=True)
def offline_network(monkeypatch):
    """Prevent a missing model from silently becoming an online download."""
    monkeypatch.setattr(socket.socket, "connect", deny_network)
    monkeypatch.setattr(socket, "create_connection", deny_network)


@pytest.fixture(autouse=True)
def no_groq_key(monkeypatch):
    """Use the offline model even if a developer has a real Groq key."""
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_MODEL", raising=False)
    monkeypatch.setattr(groq, "KEY_FILE", "no-key-during-tests.txt")


@pytest.fixture
def song(tmp_path):
    """Provide a nonempty MP3 path; engine tests mock its encoded contents."""
    path = tmp_path / "song.mp3"
    path.write_bytes(b"fixture audio")
    return path


@pytest.fixture
def desktop(qapp):
    """Dispose windows only after any native worker has stopped."""
    instance = window.Window()
    instance.show()
    yield instance
    instance.runner.cancel()
    helpers.wait_runner(instance.runner, qapp)
    instance.close()
    instance.deleteLater()
    QtCore.QCoreApplication.sendPostedEvents(
        None, QtCore.QEvent.Type.DeferredDelete
    )
