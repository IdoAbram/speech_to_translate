"""The four-screen workflow with real Qt workers and fake models."""

import types
from unittest import mock

import pytest
from PySide6 import QtCore, QtGui, QtWidgets

from speech_translate import config, settings, speech, translation
from speech_translate.gui import (
    drop_area,
    key_dialog,
    language_bar,
    lyrics_table,
    settings_dialog,
    worker,
)
from speech_translate.translation import groq
from tests import helpers

WORDS = "Tylko jedno w głowie mam\n\nW krainę zapomnienia"


@pytest.fixture
def heard(monkeypatch):
    """Recognize two Polish lines separated by a verse break."""
    transcribe = mock.Mock(
        return_value=types.SimpleNamespace(text=WORDS, language="pl")
    )
    monkeypatch.setattr(speech, "transcribe", transcribe)
    return transcribe


@pytest.fixture
def translator(monkeypatch):
    """Translate by upper-casing, keeping every line in place."""
    translate = mock.Mock(side_effect=lambda text, *a, **k: text.upper())
    monkeypatch.setattr(translation, "translate", translate)
    return translate


@pytest.fixture
def translated(desktop, song, heard, translator, qapp):
    """Run the whole flow: choose a song, then click the big Translate."""
    desktop.accept_file(str(song))
    desktop.view.chosen.translate.click()
    helpers.wait_runner(desktop.runner, qapp)
    return desktop


def test_choose_hear_and_translate(translated, heard, translator):
    """One click hears the song in its language, then translates it."""
    view = translated.view
    assert view.page() == "result"
    assert heard.call_args.args[1] == "pl"
    assert translator.call_args.args[1:3] == ("pl", "he")
    assert view.result.table.translated_lines() == WORDS.upper().split("\n")
    assert view.status.property("kind") == "success"


def test_screens_follow_the_flow(desktop, song, heard, translator, qapp):
    """Start, chosen, working, then result."""
    assert desktop.view.page() == "start"
    desktop.accept_file(str(song))
    assert desktop.view.page() == "chosen"
    assert desktop.view.chosen.song.text() == song.name
    desktop.start()
    assert desktop.view.page() == "working" and desktop.runner.busy
    helpers.wait_runner(desktop.runner, qapp)
    assert desktop.view.page() == "result"


def test_click_copies_a_line(translated):
    """Clicking a row copies its translation and names the line."""
    table = translated.view.result.table
    table.cellClicked.emit(2, lyrics_table.TRANSLATION)
    clipboard = QtWidgets.QApplication.clipboard()
    assert clipboard.text() == "W KRAINĘ ZAPOMNIENIA"
    assert "2" in translated.view.status.text()
    assert table.item(2, lyrics_table.HINT).text() == "Copied ✓"
    translated.copy_all()
    assert clipboard.text() == WORDS.upper()


def test_switching_back_reuses_translation(translated, translator, qapp):
    """Hebrew, English, then Hebrew again runs the model only twice."""
    languages = translated.view.result.languages
    for target in ("en", "he"):
        languages.set_languages("pl", target)
        translated.translate_again()
        helpers.wait_runner(translated.runner, qapp)
    assert [c.args[2] for c in translator.call_args_list] == ["he", "en"]
    assert translated.view.page() == "result"


def test_new_song_language_is_heard_again(translated, heard, qapp):
    """Correcting the song's language listens to the song again."""
    translated.view.result.languages.set_languages("en", "he")
    translated.translate_again()
    helpers.wait_runner(translated.runner, qapp)
    assert [c.args[1] for c in heard.call_args_list] == ["pl", "en"]


def test_fallback_is_shown_but_not_remembered(
    desktop, song, heard, monkeypatch, qapp
):
    """Explain an offline fallback and try Groq again next time."""
    calls = []
    monkeypatch.setattr(translation, "translate", fallback(calls))
    desktop.accept_file(str(song))
    for _ in range(2):
        desktop.start()
        helpers.wait_runner(desktop.runner, qapp)
    assert len(calls) == 2
    assert desktop.view.status.property("kind") == "warning"
    assert "offline model" in desktop.view.status.text()


def fallback(calls):
    """Simulate a translation that had to fall back to the offline model."""

    def translate(text, *args, notice, **kwargs):
        calls.append(text)
        notice("Groq was unavailable. Used the offline model.")
        return text

    return translate


def test_failures_return_to_a_useful_screen(desktop, song, heard, qapp):
    """A translation error keeps the words; a hearing error asks again."""
    with mock.patch.object(translation, "translate", side_effect=missing):
        desktop.accept_file(str(song))
        desktop.start()
        helpers.wait_runner(desktop.runner, qapp)
    assert desktop.view.page() == "result"
    assert desktop.view.status.property("kind") == "error"
    assert desktop.view.result.table.source_lines() == WORDS.split("\n")
    heard.side_effect = config.AppError("Bad audio")
    desktop.accept_file(str(song))
    desktop.start()
    helpers.wait_runner(desktop.runner, qapp)
    assert desktop.view.page() == "chosen"
    assert "Bad audio" in desktop.view.status.text()


def missing(*args, **kwargs):
    """Simulate a recoverable missing model."""
    raise config.AppError("Missing model")


def test_fixing_a_word_clears_the_translation(translated):
    """A corrected line never sits beside an old translation."""
    table = translated.view.result.table
    table.item(0, lyrics_table.SOURCE).setText("Tylko jedno w głowie")
    assert not any(table.translated_lines())
    assert "Translate" in translated.view.status.text()


def test_new_song_and_another_song(translated, song):
    """Both buttons return to the 'choose a song' screen."""
    translated.view.result.new_song.emit()
    assert translated.view.page() == "start" and translated.path == ""
    translated.accept_file(str(song))
    translated.view.chosen.other_song.emit()
    assert translated.view.page() == "start"


def drag_events(path):
    """Build drag events; the caller keeps the returned mime data alive."""
    mime = QtCore.QMimeData()
    mime.setUrls([QtCore.QUrl.fromLocalFile(str(path))])
    args = (
        QtCore.QPointF(5, 5),
        QtCore.Qt.DropAction.CopyAction,
        mime,
        QtCore.Qt.MouseButton.LeftButton,
        QtCore.Qt.KeyboardModifier.NoModifier,
    )
    return mime, QtGui.QDragEnterEvent(*args), QtGui.QDropEvent(*args)


@pytest.mark.parametrize("target", ["window", "card"])
def test_dropping_an_mp3(desktop, song, target):
    """Drop a song on the window or on the big card."""
    widget = desktop if target == "window" else desktop.view.drop
    mime, enter, drop = drag_events(song)  # mime must outlive the events
    widget.dragEnterEvent(enter)
    widget.dropEvent(drop)
    assert enter.isAccepted() and drop.isAccepted()
    assert desktop.view.page() == "chosen"


def test_drop_validation(song, tmp_path):
    """Reject non-MP3 and multi-file drops before starting a worker."""
    mime = QtCore.QMimeData()
    mime.setUrls([QtCore.QUrl.fromLocalFile(str(song))])
    assert drop_area.dropped_mp3(mime) == str(song)
    other = tmp_path / "song.wav"
    other.write_bytes(b"wav")
    mime.setUrls([QtCore.QUrl.fromLocalFile(str(other))])
    assert drop_area.dropped_mp3(mime) == ""


def test_file_picker_and_invalid_file(desktop, song, monkeypatch):
    """The big card opens a picker; a non-MP3 file is explained."""
    monkeypatch.setattr(
        QtWidgets.QFileDialog, "getOpenFileName", lambda *a: (str(song), "")
    )
    desktop.view.drop.click()
    assert desktop.view.page() == "chosen"
    desktop.new_song()
    desktop.accept_file("song.wav")
    assert "MP3" in desktop.view.status.text()
    assert desktop.view.page() == "start"


def test_save_translation(translated, tmp_path, monkeypatch):
    """Save the translation as UTF-8 text, and explain a failure."""
    target = tmp_path / "out.txt"
    dialog = QtWidgets.QFileDialog
    monkeypatch.setattr(dialog, "getSaveFileName", lambda *a: (str(target), ""))
    translated.save_translation()
    assert target.read_text(encoding="utf-8-sig") == WORDS.upper()
    monkeypatch.setattr(
        dialog, "getSaveFileName", lambda *a: (str(tmp_path), "")
    )
    translated.save_translation()
    assert translated.view.status.property("kind") == "error"


def wait_for_cancel(*args, **kwargs):
    """Keep a fake operation alive until the controller cancels it."""
    assert kwargs["cancel"].wait(3), "Cancellation was not delivered"
    raise config.Cancelled("Cancelled")


def test_cancel_returns_calmly(desktop, song, monkeypatch, qapp):
    """Cancel stops the work and shows a calm, not an error, message."""
    monkeypatch.setattr(speech, "transcribe", wait_for_cancel)
    desktop.accept_file(str(song))
    desktop.start()
    with pytest.raises(RuntimeError):
        desktop.runner.start(worker.Request("speech", "en", path=str(song)))
    desktop.view.activity.cancel.click()
    helpers.wait_runner(desktop.runner, qapp)
    assert desktop.view.page() == "chosen"
    assert desktop.view.status.property("kind") == "info"


def test_close_cancels_and_waits(desktop, song, monkeypatch, qapp):
    """A close request never destroys a running native thread."""
    monkeypatch.setattr(speech, "transcribe", wait_for_cancel)
    desktop.accept_file(str(song))
    desktop.start()
    desktop.close()
    assert desktop.close_pending
    helpers.wait_runner(desktop.runner, qapp)
    assert not desktop.isVisible()


def test_progress_maps_onto_one_bar(desktop):
    """Hearing fills the first 70%, translating the rest."""
    activity = desktop.view.activity
    desktop.action = "speech"
    desktop.show_progress("Loading", -1)
    assert activity.status.text() == "Reading the song…"
    desktop.show_progress("Heard half", 50)
    assert activity.highwater == 35
    desktop.action = "translate"
    desktop.show_progress("Translated half", 50)
    assert activity.highwater == 85
    assert activity.status.text() == "Translating…"


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


def paste(key):
    """Simulate pasting a key and pressing Save in the key dialog."""

    def run(dialog):
        dialog.field.setText(key)
        dialog.save()
        return dialog.result()

    return run


def test_online_switch_asks_for_a_key(desktop, monkeypatch):
    """Turning online translation on without a key asks for one."""
    dialog = settings_dialog.SettingsDialog(desktop)
    dialog.online_changed.connect(lambda on: desktop.set_online(on, dialog))
    assert dialog.online_state.text() == "Off"
    monkeypatch.setattr(key_dialog.KeyDialog, "exec", paste("gsk_test"))
    dialog.online.setChecked(True)
    assert groq.active_key() == "gsk_test"
    assert dialog.online_state.text() == "On"
    assert "saved" in dialog.key_state.text()
    dialog.online.setChecked(False)
    assert groq.active_key() == "" and groq.api_key() == "gsk_test"
    assert not settings.online_enabled()


def test_online_switch_stays_off_without_a_key(desktop, monkeypatch):
    """Cancelling the key dialog leaves online translation off."""
    dialog = settings_dialog.SettingsDialog(desktop)
    dialog.online_changed.connect(lambda on: desktop.set_online(on, dialog))
    monkeypatch.setattr(key_dialog.KeyDialog, "exec", lambda self: 0)
    dialog.online.setChecked(True)
    assert not dialog.online.isChecked()
    assert not settings.online_enabled()


def test_settings_buttons(desktop, monkeypatch):
    """Settings can switch full screen and replace the key."""
    monkeypatch.setattr(key_dialog.KeyDialog, "exec", paste("gsk_new"))
    monkeypatch.setattr(settings_dialog.SettingsDialog, "exec", use_buttons)
    desktop.view.settings_requested.emit()
    assert desktop.isFullScreen()
    assert groq.api_key() == "gsk_new"


def use_buttons(dialog):
    """Press Full screen and Change key, then close the dialog."""
    dialog.fullscreen_requested.emit()
    dialog.key_requested.emit()
    return 1


def test_bad_paste_keeps_dialog_open(qapp):
    """Explain a broken paste instead of saving it."""
    dialog = key_dialog.KeyDialog()
    dialog.field.setText("two keys")
    dialog.save()
    assert "without spaces" in dialog.message.text()
    assert dialog.result() == 0 and not groq.user_key_path().exists()


def test_language_bar_keeps_languages_apart(qapp):
    """The song's language is hidden among the translation languages."""
    bar = language_bar.LanguageBar()
    assert (bar.source(), bar.target()) == ("pl", "he")
    assert bar.target_buttons["pl"].isHidden()
    bar.source_buttons["he"].click()
    assert (bar.source(), bar.target()) == ("he", "en")
    bar.set_languages("en", "en")
    assert bar.target() == "he"


def test_lyrics_table_numbers_hover_and_copy(qapp):
    """Number only real lines; hovering and copying mark one row."""
    table = lyrics_table.LyricsTable()
    table.set_lines(["a", "", "b"], ["A", "", "B"])
    assert table.is_blank(1) and table.line_number(2) == 2
    table.cellEntered.emit(0, lyrics_table.SOURCE)
    assert table.item(0, lyrics_table.HINT).text() == "Click to copy"
    table.leaveEvent(QtCore.QEvent(QtCore.QEvent.Type.Leave))
    assert table.item(0, lyrics_table.HINT).text() == ""
    clicked = []
    table.line_clicked.connect(clicked.append)
    table.cellClicked.emit(1, lyrics_table.SOURCE)
    table.cellClicked.emit(2, lyrics_table.SOURCE)
    assert clicked == [2]
