"""Connect the choose, transcribe, review, and translate workflow."""

import pathlib

from PySide6 import QtGui, QtWidgets

from speech_translate import config, i18n, speech
from speech_translate.gui import jobs, key_dialog, settings_dialog, view, worker
from speech_translate.translation import cache, groq


class Window(QtWidgets.QMainWindow):
    """Coordinate user actions while all inference runs in a worker."""

    def __init__(self):
        """Start with no song selected and no loaded models."""
        super().__init__()
        self.setWindowTitle("SongWords")
        self.resize(1000, 720)
        self.view = view.View()
        self.runner = jobs.JobRunner(self)
        self.path = ""
        self.action = ""
        self.language = None
        self.source_override = None
        self.close_pending = False
        self.translations = cache.TranslationCache()
        self.pending_translation = None
        self.result_notice = ""
        self.setCentralWidget(self.view)
        self._connect_controls()
        self._connect_jobs()
        self._connect_window()

    def _connect_window(self) -> None:
        """Offer Settings and Exit buttons, plus full-screen shortcuts."""
        self.view.settings_requested.connect(self.open_settings)
        self.view.close_requested.connect(self.close)
        QtGui.QShortcut("F11", self, activated=self.toggle_fullscreen)
        QtGui.QShortcut("Escape", self, activated=self.showMaximized)

    def toggle_fullscreen(self) -> None:
        """Allow normal desktop multitasking without losing the current song."""
        if self.isFullScreen():
            self.showMaximized()
        else:
            self.showFullScreen()

    def _connect_controls(self) -> None:
        """Connect only user-facing actions to the controller."""
        self.view.drop.selected.connect(self.accept_file)
        self.view.target_chosen.connect(self.choose_target)
        self.view.original.changed.connect(self.clear_translation)
        self.view.cancel_button.clicked.connect(self.cancel_job)
        self.view.original.notice.connect(self.view.show_status)
        self.view.translated.notice.connect(self.view.show_status)

    def _connect_jobs(self) -> None:
        """Keep updates and results on the GUI thread."""
        self.runner.progress.connect(self.view.show_progress)
        self.runner.notice.connect(self.keep_notice)
        self.runner.result.connect(self.show_result)
        self.runner.failed.connect(self.show_error)
        self.runner.busy_changed.connect(self.busy_changed)

    def show_error(self, message: str) -> None:
        """Show a failure in the red status bar."""
        self.view.show_status(message, "error")

    def accept_file(self, path: str) -> None:
        """Start recognition immediately after a valid MP3 is selected."""
        if self.runner.busy:
            return
        if pathlib.Path(path).suffix.lower() != ".mp3":
            self.show_error(i18n.tr("Please choose an MP3 file."))
            return
        self.path = path
        self.language = None
        name = pathlib.Path(path).name
        self.view.drop.setText(
            i18n.tr("{name} · click to choose another song", name=name)
        )
        self.view.drop.setToolTip(path)
        self.view.original.set_text("", self.source_override)
        self.view.show_transcript(False)
        request = worker.Request("speech", self.source_override, path=path)
        self._start(request)

    def _start(self, request: worker.Request) -> None:
        """Capture the current action and start a single background job."""
        self.action = request.action
        self.result_notice = ""
        self.view.show_progress(i18n.tr("Loading…"), -1)
        self.runner.start(request)

    def choose_target(self, code: str) -> None:
        """Translate into the language whose button was clicked."""
        if self.runner.busy:
            return
        self.view.select_target(code)
        self.translate_text()

    def translate_text(self) -> None:
        """Translate the edited words, reusing any earlier result."""
        if self.runner.busy:
            return
        text = self.view.original.text()
        if not text.strip():
            self.show_error(i18n.tr("There are no words to translate yet."))
            return
        self.clear_translation()
        key = (text, self.language, self.view.target())
        remembered = self.translations.get(*key)
        if remembered is not None:
            self.show_translation(remembered)
            self.view.show_status(self._ready_message(), "success")
            return
        self.pending_translation = key
        self._start(worker.Request("translate", key[1], key[2], text=text))

    def show_result(self, result: speech.Transcript | str) -> None:
        """Show the song's words first, then both texts after translation."""
        if self.action == "speech":
            self.show_transcript(result)
        else:
            self.finish_translation(result)

    def keep_notice(self, message: str) -> None:
        """Remember how the running job produced its result."""
        self.result_notice = message

    def finish_translation(self, result: str) -> None:
        """Show a result; never remember a lower-quality fallback."""
        self.show_translation(result)
        if self.result_notice:
            self.view.show_status(self.result_notice, "warning")
            return
        if self.pending_translation is not None:
            self.translations.put(*self.pending_translation, result)
        self.view.show_status(self._ready_message(), "success")

    def show_translation(self, text: str) -> None:
        """Display a translation beside the words it came from."""
        self.view.translated.set_text(text, self.view.target())
        self.view.translated.show()
        self.view.panels.setSizes([1, 1])

    def _ready_message(self) -> str:
        """Explain that numbered lines match between the two texts."""
        return i18n.tr(
            "Translation ready. Line numbers match the song's lines."
        )

    def show_transcript(self, result: speech.Transcript) -> None:
        """Show the words and offer the other languages for translation."""
        self.language = result.language
        self.view.original.set_text(result.text, result.language)
        self.view.show_transcript(True)
        self.view.detected.setText(self._language_message(result))
        self.view.set_song_language(result.language)
        self.view.select_target("en" if result.language == "he" else "he")
        self.view.show_status(
            i18n.tr("Words ready. Fix any mistakes, then choose a language."),
            "success",
        )

    def _language_message(self, result: speech.Transcript) -> str:
        """Name the song's language, flagging an uncertain detection."""
        name = config.language_name(result.language)
        if result.confidence < 0.7:
            return i18n.tr(
                "Song language: {name} (check in Settings)", name=name
            )
        return i18n.tr("Song language: {name}", name=name)

    def open_settings(self) -> None:
        """Change the song language or online translation in one place."""
        dialog = settings_dialog.SettingsDialog(
            self.source_override, bool(groq.api_key()), self
        )
        dialog.key_requested.connect(lambda: self.edit_groq_key(dialog))
        dialog.fullscreen_requested.connect(self.toggle_fullscreen)
        dialog.exec()
        self.apply_song_language(dialog.source())

    def apply_song_language(self, source: str | None) -> None:
        """Read the song again when its language was corrected."""
        if source == self.source_override:
            return
        self.source_override = source
        if self.path and not self.runner.busy:
            self.accept_file(self.path)

    def edit_groq_key(self, settings=None) -> None:
        """Turn Groq on or off; earlier results may come from another model."""
        if not key_dialog.KeyDialog(self).exec():
            return
        self.translations = cache.TranslationCache()
        self.clear_translation()
        online = bool(groq.api_key())
        if settings is not None:
            settings.show_online(online)
        self.view.show_status(
            i18n.tr("Online translation is on.")
            if online
            else i18n.tr("Online translation is off."),
            "success",
        )

    def clear_translation(self) -> None:
        """Never show an old result beside edited words."""
        self.view.translated.set_text("", self.view.target())
        self.view.translated.hide()

    def busy_changed(self, busy: bool) -> None:
        """Restore controls or finish a deferred close after worker cleanup."""
        self.view.set_busy(busy)
        if not busy and self.close_pending:
            self.close()

    def cancel_job(self) -> None:
        """Request cancellation after the current inference step completes."""
        self.runner.cancel()
        self.view.cancel_button.setEnabled(False)
        self.view.show_status(i18n.tr("Cancelling after the current step…"))

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Avoid destroying a running native model thread."""
        if self.runner.busy:
            self.close_pending = True
            self.cancel_job()
            event.ignore()
        else:
            event.accept()
