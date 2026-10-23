"""Connect the four screens: choose, pick languages, work, read and copy."""

import pathlib

from PySide6 import QtGui, QtWidgets

from speech_translate import config, i18n, settings, speech
from speech_translate.gui import (
    drop_area,
    jobs,
    key_dialog,
    settings_dialog,
    view,
    worker,
)
from speech_translate.translation import cache, groq

SPEECH_SHARE = 70


class Window(QtWidgets.QMainWindow):
    """Coordinate user actions while all inference runs in a worker."""

    def __init__(self):
        """Start on the 'choose a song' screen with no models loaded."""
        super().__init__()
        self.setWindowTitle("SongWords")
        self.resize(1200, 800)
        self.setAcceptDrops(True)
        self.view = view.View()
        self.runner = jobs.JobRunner(self)
        self.translations = cache.TranslationCache()
        self.close_pending = False
        self._reset_song("")
        self.setCentralWidget(self.view)
        self._connect_top_bar()
        self._connect_screens()
        self._connect_jobs()

    def _reset_song(self, path: str) -> None:
        """Forget everything about the previous song."""
        self.path = path
        self.action = ""
        self.heard_language = None
        self.next_translation = None
        self.pending_translation = None
        self.result_notice = ""
        self.cancel_requested = False

    def _connect_top_bar(self) -> None:
        """Full screen, Settings, and Exit, plus keyboard shortcuts."""
        self.view.fullscreen_requested.connect(self.toggle_fullscreen)
        self.view.settings_requested.connect(self.open_settings)
        self.view.close_requested.connect(self.close)
        QtGui.QShortcut("F11", self, activated=self.toggle_fullscreen)
        QtGui.QShortcut("Escape", self, activated=self.showMaximized)

    def _connect_screens(self) -> None:
        """Connect each screen's buttons to the matching action."""
        self.view.drop.selected.connect(self.accept_file)
        self.view.chosen.other_song.connect(self.new_song)
        self.view.chosen.translate_requested.connect(self.start)
        self.view.activity.cancel.clicked.connect(self.cancel_job)
        result = self.view.result
        result.new_song.connect(self.new_song)
        result.translate_requested.connect(self.translate_again)
        result.copy_all.connect(self.copy_all)
        result.save.connect(self.save_translation)
        result.table.line_clicked.connect(self.copy_line)
        result.table.edited.connect(self.words_edited)

    def _connect_jobs(self) -> None:
        """Keep updates and results on the GUI thread."""
        self.runner.progress.connect(self.show_progress)
        self.runner.notice.connect(self.keep_notice)
        self.runner.result.connect(self.show_result)
        self.runner.failed.connect(self.job_failed)
        self.runner.busy_changed.connect(self.busy_changed)

    def toggle_fullscreen(self) -> None:
        """Allow normal desktop multitasking without losing the current song."""
        if self.isFullScreen():
            self.showMaximized()
        else:
            self.showFullScreen()

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        """Accept an MP3 dropped anywhere on the window."""
        if not self.runner.busy and drop_area.dropped_mp3(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        """Choose the dropped song."""
        path = drop_area.dropped_mp3(event.mimeData())
        if path and not self.runner.busy:
            event.acceptProposedAction()
            self.accept_file(path)

    def accept_file(self, path: str) -> None:
        """Show the chosen song and ask for its languages."""
        if self.runner.busy:
            return
        if pathlib.Path(path).suffix.lower() != ".mp3":
            self.view.show_status(
                i18n.tr("Please choose an MP3 file."), "error"
            )
            return
        self._reset_song(path)
        name = pathlib.Path(path).name
        for screen in (self.view.chosen, self.view.result, self.view.activity):
            screen.set_song(name)
        self.view.status.clear_message()
        self.view.show_page("chosen")

    def new_song(self) -> None:
        """Go back to the 'choose a song' screen."""
        if not self.runner.busy:
            self._reset_song("")
            self.view.status.clear_message()
            self.view.show_page("start")

    def start(self) -> None:
        """Hear the song in its language, then translate it."""
        languages = self.view.chosen.languages
        self._sync_languages(languages.source(), languages.target())
        self._listen()

    def translate_again(self) -> None:
        """Translate the shown words, hearing them again in a new language."""
        languages = self.view.result.languages
        self._sync_languages(languages.source(), languages.target())
        if languages.source() != self.heard_language:
            self._listen()
        else:
            self._translate("\n".join(self.view.result.table.source_lines()))

    def _sync_languages(self, source: str, target: str) -> None:
        """Show the same languages on both screens."""
        self.view.chosen.languages.set_languages(source, target)
        self.view.result.languages.set_languages(source, target)
        self.view.result.table.set_headers(
            config.language_name(source), config.language_name(target)
        )

    def _listen(self) -> None:
        """Start speech recognition, with translation queued after it."""
        source = self.view.chosen.languages.source()
        self.next_translation = True
        self.view.activity.set_stage(0)
        self._start(worker.Request("speech", source, path=self.path))

    def _translate(self, text: str) -> None:
        """Translate words, showing a remembered result instantly."""
        languages = self.view.result.languages
        key = (text, languages.source(), languages.target())
        remembered = self.translations.get(*key)
        if remembered is not None:
            self._show_translation(remembered, "")
            return
        self.pending_translation = key
        self.view.activity.set_stage(2)
        self._start(worker.Request("translate", key[1], key[2], text=text))

    def _start(self, request: worker.Request) -> None:
        """Show the working screen and start one background job."""
        self.action = request.action
        self.result_notice = ""
        self.cancel_requested = False
        self.view.status.clear_message()
        self.view.show_page("working")
        self.runner.start(request)

    def show_progress(self, message: str, percent: int) -> None:
        """Map each job onto one bar: hearing first, translating last."""
        if self.action == "speech":
            self.view.activity.set_stage(0 if percent < 0 else 1)
            overall = percent * SPEECH_SHARE // 100 if percent >= 0 else -1
        else:
            self.view.activity.set_stage(2)
            share = 100 - SPEECH_SHARE
            overall = SPEECH_SHARE + percent * share // 100
            overall = overall if percent >= 0 else -1
        self.view.show_progress(message, overall)

    def show_result(self, result: speech.Transcript | str) -> None:
        """Show heard words, or a finished translation."""
        if self.action == "speech":
            self._words_heard(result)
        else:
            self._show_translation(result, self.result_notice)

    def _words_heard(self, transcript: speech.Transcript) -> None:
        """Show the words and queue their translation."""
        self.heard_language = transcript.language
        self.view.result.table.set_lines(transcript.text.split("\n"))
        if self.next_translation:
            self.next_translation = transcript.text

    def _show_translation(self, text: str, notice: str) -> None:
        """Show the translation; never remember a lower-quality fallback."""
        table = self.view.result.table
        table.set_lines(table.source_lines(), text.split("\n"))
        if not notice and self.pending_translation is not None:
            self.translations.put(*self.pending_translation, text)
        self.pending_translation = None
        self.view.show_page("result")
        message = notice or i18n.tr(
            "Translation ready. Click a line to copy its translation."
        )
        self.view.show_status(message, "warning" if notice else "success")

    def keep_notice(self, message: str) -> None:
        """Remember how the running job produced its result."""
        self.result_notice = message

    def job_failed(self, message: str) -> None:
        """Explain a failure and return to the last useful screen."""
        self.next_translation = None
        heard = self.view.result.table.rowCount() and self.heard_language
        self.view.show_page("result" if heard else "chosen")
        kind = "info" if self.cancel_requested else "error"
        self.view.show_status(message, kind)

    def busy_changed(self, busy: bool) -> None:
        """Start a queued translation, or finish a deferred close."""
        self.view.set_busy(busy)
        if busy:
            return
        if self.close_pending:
            self.close()
        elif isinstance(self.next_translation, str):
            text, self.next_translation = self.next_translation, None
            self._translate(text)

    def copy_line(self, row: int) -> None:
        """Copy one line's translation, or the song line before translating."""
        table = self.view.result.table
        text = table.translated_lines()[row] or table.source_lines()[row]
        QtWidgets.QApplication.clipboard().setText(text)
        table.mark_copied(row)
        number = table.line_number(row)
        self.view.show_status(
            i18n.tr(
                "Line {number} copied. You can paste it in the video editor.",
                number=number,
            ),
            "success",
        )

    def copy_all(self) -> None:
        """Copy the whole translation, keeping its lines and verse breaks."""
        QtWidgets.QApplication.clipboard().setText(self._export_text())
        self.view.show_status(i18n.tr("All lines copied."), "success")

    def _export_text(self) -> str:
        """Return the translation if there is one, else the song's words."""
        table = self.view.result.table
        translated = table.translated_lines()
        lines = translated if any(translated) else table.source_lines()
        return "\n".join(lines)

    def save_translation(self) -> None:
        """Save the translation as a text file the video editor can read."""
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            i18n.tr("Save text"),
            "translation.txt",
            i18n.tr("Text files (*.txt)"),
        )
        if path:
            self._write_text(pathlib.Path(path))

    def _write_text(self, path: pathlib.Path) -> None:
        """Write Windows-friendly UTF-8, reporting any file-system problem."""
        try:
            path.write_text(self._export_text(), encoding="utf-8-sig")
        except OSError as error:
            message = i18n.tr("Could not save: {error}", error=error)
            self.view.show_status(message, "error")
            return
        self.view.show_status(
            i18n.tr("Saved {name}", name=path.name), "success"
        )

    def words_edited(self) -> None:
        """Clear a translation that no longer matches the corrected words."""
        self.view.result.table.clear_translation()
        self.view.show_status(
            i18n.tr("The words changed. Click Translate to translate again.")
        )

    def open_settings(self) -> None:
        """Change online translation or the window size."""
        dialog = settings_dialog.SettingsDialog(self)
        dialog.key_requested.connect(lambda: self.edit_groq_key(dialog))
        dialog.online_changed.connect(lambda on: self.set_online(on, dialog))
        dialog.fullscreen_requested.connect(self.toggle_fullscreen)
        dialog.exec()

    def set_online(self, enabled: bool, dialog) -> None:
        """Switch online translation, asking for a key if none is saved."""
        settings.set_online_enabled(enabled)
        self.translations = cache.TranslationCache()
        if enabled and not groq.api_key():
            self.edit_groq_key(dialog)
        if enabled and not groq.api_key():
            settings.set_online_enabled(False)
        dialog.refresh()

    def edit_groq_key(self, dialog=None) -> None:
        """Save or remove the Groq key; earlier results may change."""
        if key_dialog.KeyDialog(self).exec():
            self.translations = cache.TranslationCache()
        if dialog is not None:
            dialog.refresh()

    def cancel_job(self) -> None:
        """Request cancellation after the current inference step completes."""
        self.cancel_requested = True
        self.runner.cancel()
        self.view.activity.cancel.setEnabled(False)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Avoid destroying a running native model thread."""
        if self.runner.busy:
            self.close_pending = True
            self.cancel_job()
            event.ignore()
        else:
            event.accept()
