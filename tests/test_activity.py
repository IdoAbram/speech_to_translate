"""The working screen: real progress, elapsed time, and plain steps."""

import time

from speech_translate import i18n
from speech_translate.gui import activity, theme


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
    assert panel.highwater == 16 and "1:05" in panel.elapsed.text()
    assert panel.percent.text() == "16%"
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


def test_steps_are_ticked_off(qtbot):
    """Earlier steps get a check mark; the current one is named."""
    panel = activity.Activity()
    qtbot.addWidget(panel)
    panel.set_song("song.mp3")
    panel.set_stage(1)
    assert panel.status.text() == "Hearing the words…"
    assert panel.step_labels[0].text().startswith("✓")
    assert panel.step_labels[1].objectName() == "stepNow"
    assert panel.step_labels[2].objectName() == "stepLater"


def test_fullscreen_toggle_and_theme(desktop, qapp):
    """Offer a visible way back to normal windows while using the theme."""
    qapp.setStyleSheet(theme.STYLESHEET)
    desktop.view.fullscreen_requested.emit()
    assert desktop.isFullScreen()
    desktop.view.fullscreen_requested.emit()
    assert desktop.isMaximized() and not desktop.isFullScreen()


def test_hebrew_steps(qtbot):
    """The working screen speaks Hebrew in the desktop app."""
    i18n.set_language("he")
    panel = activity.Activity()
    qtbot.addWidget(panel)
    panel.set_stage(2)
    assert panel.status.text() == "מתרגם…"
