"""Connect the drop, transcribe, review, and translate workflow."""

import pathlib

from PySide6 import QtGui, QtWidgets

from speech_translate import config, speech
from speech_translate.gui import jobs, view, worker
from speech_translate.translation import cache


class Window(QtWidgets.QMainWindow):
    """Coordinate user actions while all inference runs in a worker."""

    def __init__(self):
        """Start with an empty song selection and no loaded models."""
        super().__init__()
        self.setWindowTitle("Speech to Translate — Offline")
        self.resize(1000, 720)
        self.view = view.View()
        self.runner = jobs.JobRunner(self)
        self.path = ""
        self.action = ""
        self.language = None
        self.close_pending = False
        self.translations = cache.TranslationCache()
        self.pending_translation = None
        self.result_notice = ""
        self.setCentralWidget(self.view)
        self._connect_controls()
        self._connect_jobs()
        self._connect_window()

    def _connect_window(self) -> None:
        """Expose fullscreen controls through visible buttons and shortcuts."""
        self.view.fullscreen_requested.connect(self.toggle_fullscreen)
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
        self.view.source.currentIndexChanged.connect(self.source_changed)
        self.view.target.currentIndexChanged.connect(self.clear_translation)
        self.view.original.changed.connect(self.clear_translation)
        self.view.translate_button.clicked.connect(self.translate_text)
        self.view.cancel_button.clicked.connect(self.cancel_job)
        self.view.original.notice.connect(self.view.status.setText)
        self.view.translated.notice.connect(self.view.status.setText)

    def _connect_jobs(self) -> None:
        """Keep updates and results on the GUI thread."""
        self.runner.progress.connect(self.view.show_progress)
        self.runner.notice.connect(self.keep_notice)
        self.runner.result.connect(self.show_result)
        self.runner.failed.connect(self.view.status.setText)
        self.runner.busy_changed.connect(self.busy_changed)

    def accept_file(self, path: str) -> None:
        """Start recognition immediately after a valid MP3 is selected."""
        if self.runner.busy:
            return
        if pathlib.Path(path).suffix.lower() != ".mp3":
            self.view.status.setText("Please choose an MP3 file.")
            return
        self.path = path
        self.language = None
        self.view.drop.setText(
            pathlib.Path(path).name + "\nChoose another song"
        )
        self.view.drop.setToolTip(path)
        self.view.original.set_text("", self.view.source.currentData())
        self.view.show_transcript(False)
        self._start(
            worker.Request("speech", self.view.source.currentData(), path=path)
        )

    def source_changed(self) -> None:
        """Transcribe the selected song again when its language changes."""
        if self.path and not self.runner.busy:
            self.accept_file(self.path)

    def _start(self, request: worker.Request) -> None:
        """Capture the current action and start a single background job."""
        self.action = request.action
        self.result_notice = ""
        self.view.show_progress("Loading…", -1)
        self.runner.start(request)

    def translate_text(self) -> None:
        """Translate the edited transcript, reusing any earlier result."""
        if self.runner.busy:
            return
        text = self.view.original.text()
        if not text.strip():
            self.view.status.setText("There is no transcript to translate.")
            return
        self.clear_translation()
        key = (text, self.language, self.view.target.currentData())
        remembered = self.translations.get(*key)
        if remembered is not None:
            self.show_translation(remembered)
            self.view.status.setText("Translation ready (remembered).")
            return
        self.pending_translation = key
        self._start(worker.Request("translate", key[1], key[2], text=text))

    def show_result(self, result: speech.Transcript | str) -> None:
        """Show a transcript first, then both texts after translation."""
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
            self.view.status.setText(self.result_notice)
            return
        if self.pending_translation is not None:
            self.translations.put(*self.pending_translation, result)
        self.view.status.setText(self._translation_notice())

    def show_translation(self, text: str) -> None:
        """Display a translation beside the transcript it came from."""
        self.view.translated.set_text(text, self.view.target.currentData())
        self.view.translated.show()
        self.view.panels.setSizes([1, 1])

    def _translation_notice(self) -> str:
        """Explain that translated lines line up with the transcript."""
        return "Translation ready. Each line matches its transcript line."

    def show_transcript(self, result: speech.Transcript) -> None:
        """Use the detected language for translation and paragraph layout."""
        self.language = result.language
        self.view.original.set_text(result.text, result.language)
        self.view.show_transcript(True)
        name = config.LANGUAGES[result.language]
        uncertain = (
            " · Check language in settings" if result.confidence < 0.7 else ""
        )
        self.view.detected.setText(f"Song language: {name}{uncertain}")
        if self.view.target.currentData() == result.language:
            target = "he" if result.language == "en" else "en"
            self.view.target.setCurrentIndex(self.view.target.findData(target))
        self.view.status.setText(
            "Transcript ready. Edit any words, then translate."
        )

    def clear_translation(self) -> None:
        """Never show an old result beside edited source text."""
        self.view.translated.set_text("", self.view.target.currentData())
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
        self.view.status.setText("Cancelling after the current model step…")

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Avoid destroying a running native model thread."""
        if self.runner.busy:
            self.close_pending = True
            self.cancel_job()
            event.ignore()
        else:
            event.accept()
