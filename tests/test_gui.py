"""User workflow, real Qt workers, file drops, and side-by-side results."""

import pytest
from PySide6 import QtCore, QtGui, QtWidgets

from speech_translate import config, speech, translation
from speech_translate.gui import drop_area, worker
from tests import helpers


@pytest.fixture
def recognized(monkeypatch):
    """Provide a short transcript through the real background worker."""
    result = speech.Transcript("en", (speech.Segment(0, 1, "Sing again"),), 1)
    monkeypatch.setattr(speech, "transcribe", lambda *args, **kwargs: result)
    return result


def test_drop_transcribe_translate(
    desktop, song, recognized, monkeypatch, qapp
):
    """Dropping a song produces editable text before translation appears."""
    monkeypatch.setattr(
        translation, "translate", lambda *args, **kwargs: "שיר שוב"
    )
    desktop.view.drop.selected.emit(str(song))
    assert desktop.runner.busy and not desktop.view.drop.isEnabled()
    helpers.wait_runner(desktop.runner, qapp)
    assert desktop.view.original.text() == recognized.text
    assert desktop.view.translated.isHidden()
    desktop.view.translate_button.click()
    helpers.wait_runner(desktop.runner, qapp)
    assert desktop.view.original.text() == recognized.text
    assert desktop.view.translated.text() == "שיר שוב"
    assert not desktop.view.translated.isHidden()


def test_switching_back_reuses_translation(
    desktop, song, recognized, monkeypatch, qapp
):
    """Hebrew, then English, then Hebrew again runs the model only twice."""
    calls = []
    monkeypatch.setattr(
        translation, "translate", lambda *a, **k: record(calls, a)
    )
    desktop.accept_file(str(song))
    helpers.wait_runner(desktop.runner, qapp)
    for target in ("he", "en", "he"):
        desktop.view.target.setCurrentIndex(
            desktop.view.target.findData(target)
        )
        desktop.translate_text()
        helpers.wait_runner(desktop.runner, qapp)
    assert [args[2] for args in calls] == ["he", "en"]
    assert desktop.view.translated.text() == "he result"
    assert "remembered" in desktop.view.status.text()


def record(calls, args):
    """Log one translation request and answer with its target language."""
    calls.append(args)
    return f"{args[2]} result"


def test_fallback_result_is_shown_but_not_remembered(
    desktop, song, recognized, monkeypatch, qapp
):
    """Explain an offline fallback and try Groq again next time."""
    calls = []
    monkeypatch.setattr(translation, "translate", fallback(calls))
    desktop.accept_file(str(song))
    helpers.wait_runner(desktop.runner, qapp)
    for _ in range(2):
        desktop.translate_text()
        helpers.wait_runner(desktop.runner, qapp)
    assert len(calls) == 2
    assert desktop.view.translated.text() == "offline"
    assert "offline model" in desktop.view.status.text()


def fallback(calls):
    """Simulate a translation that had to fall back to the offline model."""

    def translate(*args, notice, **kwargs):
        calls.append(args)
        notice("Groq was unavailable. Used the offline model.")
        return "offline"

    return translate


def test_translation_failure_keeps_transcript(
    desktop, song, recognized, monkeypatch, qapp
):
    """Allow retries after a translation model reports an error."""
    desktop.accept_file(str(song))
    helpers.wait_runner(desktop.runner, qapp)
    monkeypatch.setattr(translation, "translate", fail_translation)
    desktop.translate_text()
    helpers.wait_runner(desktop.runner, qapp)
    assert desktop.view.original.text() == recognized.text
    assert "Missing model" in desktop.view.status.text()
    assert desktop.view.translate_button.isEnabled()


def fail_translation(*args, **kwargs):
    """Simulate a recoverable missing model."""
    raise config.AppError("Missing model")


def test_edits_clear_stale_result(desktop):
    """Clear old results when source text or target language changes."""
    desktop.view.translated.set_text("Old result", "en")
    desktop.view.original.set_text("Changed source", "en")
    assert desktop.view.translated.text() == ""
    desktop.view.translated.set_text("Another result", "en")
    desktop.view.target.setCurrentIndex(2)
    assert desktop.view.translated.text() == ""


def test_readonly_hebrew_layout(desktop, qapp, recognized):
    """Set document defaults as well as paragraph formats for Hebrew."""
    panel = desktop.view.translated
    desktop.action = "speech"
    desktop.show_result(recognized)
    desktop.action = "translate"
    desktop.show_result("שלום\nעולם")
    qapp.processEvents()
    options = panel.editor.document().defaultTextOption()
    assert options.textDirection() == QtCore.Qt.LayoutDirection.RightToLeft
    assert options.alignment() & QtCore.Qt.AlignmentFlag.AlignRight
    assert panel.text() == "שלום\nעולם"
    line = panel.editor.document().firstBlock().layout().lineAt(0)
    assert line.naturalTextRect().left() > 0


def test_hebrew_export_and_direction(desktop, tmp_path, monkeypatch):
    """Keep RTL text in logical order with unchanged stanza spacing."""
    text = "שלום עולם\nשוב\n\nשלום"
    panel = desktop.view.original
    panel.set_text(text, "he")
    block = panel.editor.document().firstBlock().blockFormat()
    assert block.alignment() & QtCore.Qt.AlignmentFlag.AlignRight
    panel.copy_text()
    assert QtWidgets.QApplication.clipboard().text() == text
    path = tmp_path / "lyrics.txt"
    monkeypatch.setattr(
        QtWidgets.QFileDialog, "getSaveFileName", lambda *args: (str(path), "")
    )
    panel.save_text()
    assert path.read_text(encoding="utf-8-sig") == text


def test_empty_export_and_save_failure(desktop, tmp_path):
    """Show inline messages for empty output and inaccessible save paths."""
    panel = desktop.view.original
    panel.save_text()
    assert "no text" in desktop.view.status.text()
    panel.set_text("Hello", "en")
    panel._write_text(str(tmp_path / "missing" / "lyrics.txt"))
    assert "Could not save" in desktop.view.status.text()


def mime_for_paths(paths):
    """Create actual Qt file-drop data."""
    mime = QtCore.QMimeData()
    mime.setUrls([QtCore.QUrl.fromLocalFile(str(path)) for path in paths])
    return mime


def test_drop_validation(song, tmp_path):
    """Reject remote URLs, multiple files, directories, and wrong types."""
    assert drop_area.dropped_mp3(mime_for_paths([song])) == str(song)
    for paths in ([song, song], [tmp_path], [tmp_path / "absent.mp3"]):
        assert drop_area.dropped_mp3(mime_for_paths(paths)) == ""
    mime = QtCore.QMimeData()
    mime.setUrls([QtCore.QUrl("https://example.com/song.mp3")])
    assert drop_area.dropped_mp3(mime) == ""


def test_native_drop_event(desktop, song, recognized, qapp):
    """Exercise the widget's drag/drop event handlers with real MIME data."""
    mime = mime_for_paths([song])
    action = QtCore.Qt.DropAction.CopyAction
    button = QtCore.Qt.MouseButton.LeftButton
    modifier = QtCore.Qt.KeyboardModifier.NoModifier
    enter = QtGui.QDragEnterEvent(
        QtCore.QPointF(5, 5), action, mime, button, modifier
    )
    drop = QtGui.QDropEvent(
        QtCore.QPointF(5, 5), action, mime, button, modifier
    )
    desktop.view.drop.dragEnterEvent(enter)
    assert enter.isAccepted()
    desktop.view.drop.dropEvent(drop)
    assert drop.isAccepted()
    helpers.wait_runner(desktop.runner, qapp)
    assert desktop.view.original.text() == recognized.text


def test_file_picker_and_language_retry(
    desktop, song, recognized, monkeypatch, qapp
):
    """Picking an MP3 and changing source language both start recognition."""
    monkeypatch.setattr(
        QtWidgets.QFileDialog, "getOpenFileName", lambda *args: (str(song), "")
    )
    desktop.view.drop.choose_file()
    helpers.wait_runner(desktop.runner, qapp)
    desktop.view.source.setCurrentIndex(desktop.view.source.findData("he"))
    assert desktop.runner.busy
    helpers.wait_runner(desktop.runner, qapp)
    assert desktop.view.original.language == recognized.language


def wait_for_cancel(*args, **kwargs):
    """Keep a fake operation alive until the controller cancels it."""
    assert kwargs["cancel"].wait(3), "Cancellation was not delivered"
    raise config.Cancelled("Cancelled")


def test_close_cancels_and_waits(desktop, song, monkeypatch, qapp):
    """A close request never destroys a running native thread."""
    monkeypatch.setattr(speech, "transcribe", wait_for_cancel)
    desktop.accept_file(str(song))
    desktop.close()
    assert desktop.close_pending
    helpers.wait_runner(desktop.runner, qapp)
    assert not desktop.isVisible()


def test_runner_rejects_concurrent_work(desktop, song, monkeypatch, qapp):
    """Keep one active model operation and recover after cancellation."""
    monkeypatch.setattr(speech, "transcribe", wait_for_cancel)
    desktop.accept_file(str(song))
    with pytest.raises(RuntimeError):
        desktop.runner.start(worker.Request("speech", "en", path=str(song)))
    desktop.cancel_job()
    helpers.wait_runner(desktop.runner, qapp)
    assert desktop.view.drop.isEnabled()


def test_invalid_input_and_empty_transcript(desktop):
    """Explain invalid user actions without starting a worker."""
    desktop.accept_file("song.wav")
    assert "MP3" in desktop.view.status.text()
    desktop.translate_text()
    assert "no transcript" in desktop.view.status.text()
    assert not desktop.runner.busy


def test_worker_unknown_action_finishes(qapp):
    """An invalid task reports an error and still signals completion."""
    task = worker.Worker(worker.Request("unknown", "en"))
    errors, completed = [], []
    task.failed.connect(errors.append)
    task.finished.connect(lambda: completed.append(True))
    task.run()
    assert "Unknown operation" in errors[0]
    assert completed == [True]


def test_unexpected_worker_error(qapp, monkeypatch):
    """Unexpected library failures also restore the application workflow."""
    task = worker.Worker(worker.Request("translate", "en", text="Hello"))
    monkeypatch.setattr(task, "_execute", raise_unexpected)
    errors = []
    task.failed.connect(errors.append)
    task.run()
    assert "Processing failed" in errors[0]


def raise_unexpected():
    """Represent a native library integration error."""
    raise TypeError("Unexpected library failure")
