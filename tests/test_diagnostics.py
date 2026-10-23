"""Executable diagnostics and launcher dispatch without downloading assets."""

import json
from unittest import mock

import pytest

from speech_translate import diagnostics, gui, launcher, speech, translation


def test_launcher_routes(monkeypatch):
    """Keep normal startup separate from explicit unattended checks."""
    monkeypatch.setattr(gui, "main", lambda: 7)
    assert launcher.main([]) == 7
    check = mock.Mock(return_value=0)
    monkeypatch.setattr(diagnostics, "main", check)
    assert launcher.main(["--self-test", "out.json"]) == 0
    check.assert_called_once_with(["out.json"])


def test_diagnostics_exercises_all_routes(monkeypatch):
    """Check six language directions and optional automatic transcription."""
    monkeypatch.setattr(diagnostics, "check_desktop", lambda: None)
    translator = mock.Mock(return_value="Translated")
    monkeypatch.setattr(translation, "translate", translator)
    transcript = speech.Transcript("en", (speech.Segment(0, 1, "Hello"),), 1)
    monkeypatch.setattr(speech, "transcribe", lambda path: transcript)
    result = diagnostics.run_checks("audio.mp3")
    assert result["ok"] and result["language"] == "en"
    assert translator.call_count == 6


@pytest.mark.parametrize("success", [True, False])
def test_diagnostics_writes_report(tmp_path, monkeypatch, success):
    """A windowed executable reports failures without relying on a console."""
    run = mock.Mock(return_value={"ok": True})
    if not success:
        run.side_effect = RuntimeError("missing bundled asset")
    monkeypatch.setattr(diagnostics, "run_checks", run)
    path = tmp_path / "report.json"
    assert diagnostics.main([str(path)]) == (0 if success else 1)
    assert json.loads(path.read_text())["ok"] is success
