"""Progress presentation, fullscreen controls, and automatic detection."""

import time

from speech_translate import speech, translation
from speech_translate.gui import activity, theme
from tests import helpers


def test_activity_tracks_real_progress_and_elapsed(qtbot, monkeypatch):
    """Keep elapsed time moving without inventing decoder progress."""
    panel = activity.Activity()
    qtbot.addWidget(panel)
    monkeypatch.setattr(time, "monotonic", lambda: 100)
    panel.set_busy(True)
    assert panel.bar.maximum() == 0
    panel.report("Audio transcribed: 0:20 / 2:00", 16)
    panel.report("Still decoding", 10)
    monkeypatch.setattr(time, "monotonic", lambda: 165)
    panel.tick()
    assert panel.highwater == 16 and "1:05 elapsed" in panel.elapsed.text()
    panel.animation.setCurrentTime(panel.animation.duration())
    assert panel.bar.value() == 16
    panel.set_busy(False)
    assert not panel.timer.isActive() and panel.bar.isHidden()


def test_new_operation_resets_progress(qtbot):
    """A new translation starts fresh after a completed transcription."""
    panel = activity.Activity()
    qtbot.addWidget(panel)
    panel.set_busy(True)
    panel.report("Done", 100)
    panel.set_busy(False)
    panel.set_busy(True)
    assert panel.highwater == 0 and panel.bar.maximum() == 0
    panel.set_busy(False)


def test_fullscreen_toggle_and_theme(desktop, qapp):
    """Offer a visible way back to normal windows while using the new theme."""
    qapp.setStyleSheet(theme.STYLESHEET)
    desktop.toggle_fullscreen()
    assert desktop.isFullScreen()
    desktop.view.fullscreen_requested.emit()
    assert desktop.isMaximized() and not desktop.isFullScreen()
    assert desktop.view.source.currentData() is None
    assert desktop.view.source.isHidden()


def test_detected_language_is_used_for_translation(
    desktop, song, monkeypatch, qapp
):
    """Translate Hebrew automatically without asking for a source language."""
    result = speech.Transcript(
        "he", (speech.Segment(0, 2, "שלום עולם"),), 2, 0.6
    )
    from unittest import mock

    translator = mock.Mock(return_value="Hello")
    monkeypatch.setattr(speech, "transcribe", lambda *args, **kw: result)
    monkeypatch.setattr(translation, "translate", translator)
    desktop.accept_file(str(song))
    helpers.wait_runner(desktop.runner, qapp)
    assert desktop.language == "he" and "Hebrew" in desktop.view.detected.text()
    assert "Check language" in desktop.view.detected.text()
    assert desktop.view.target.currentData() == "en"
    desktop.translate_text()
    helpers.wait_runner(desktop.runner, qapp)
    assert translator.call_args.args[1:3] == ("he", "en")
