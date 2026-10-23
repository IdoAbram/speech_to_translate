"""Large, step-by-step layout; behavior stays in the window module."""

from PySide6 import QtCore, QtWidgets

from speech_translate import config, i18n
from speech_translate.gui import activity, drop_area, text_panel


class View(QtWidgets.QWidget):
    """Choose a song, check its words, pick a language, read both texts."""

    settings_requested = QtCore.Signal()
    close_requested = QtCore.Signal()
    target_chosen = QtCore.Signal(str)

    def __init__(self):
        """Start with only the welcome text and the song chooser."""
        super().__init__()
        self.setObjectName("workspace")
        self.layout_box = QtWidgets.QVBoxLayout(self)
        self.layout_box.setContentsMargins(40, 24, 40, 24)
        self.layout_box.setSpacing(16)
        self._add_top_bar()
        self._add_welcome()
        self._add_song_step()
        self._add_language_step()
        self._add_texts()
        self._add_status()
        self.empty_space = QtWidgets.QWidget()
        self.layout_box.addWidget(self.empty_space, 1)
        self.show_transcript(False)

    def _add_top_bar(self) -> None:
        """Keep the app name, Settings, and Exit in one quiet row."""
        row = QtWidgets.QHBoxLayout()
        name = QtWidgets.QLabel("SongWords")
        name.setObjectName("eyebrow")
        row.addWidget(name)
        row.addStretch(1)
        for label, signal in (
            (i18n.tr("Settings"), self.settings_requested),
            (i18n.tr("Exit"), self.close_requested),
        ):
            button = QtWidgets.QPushButton(label)
            button.clicked.connect(signal.emit)
            row.addWidget(button)
        self.layout_box.addLayout(row)

    def _add_welcome(self) -> None:
        """Greet the user and explain the three steps in one sentence."""
        self.welcome = QtWidgets.QWidget()
        column = QtWidgets.QVBoxLayout(self.welcome)
        column.setContentsMargins(0, 0, 0, 0)
        title = QtWidgets.QLabel(i18n.tr("Every song has a story."))
        title.setObjectName("hero")
        subtitle = QtWidgets.QLabel(
            i18n.tr("Choose a song, check its words, and translate them.")
        )
        subtitle.setObjectName("subtitle")
        column.addWidget(title)
        column.addWidget(subtitle)
        self.layout_box.addWidget(self.welcome)

    def _add_song_step(self) -> None:
        """Step 1: the large song chooser and the detected language."""
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self._step_label(i18n.tr("1. Choose a song")), 1)
        self.detected = QtWidgets.QLabel()
        self.detected.setObjectName("subtitle")
        row.addWidget(self.detected)
        self.layout_box.addLayout(row)
        self.drop = drop_area.DropArea()
        self.layout_box.addWidget(self.drop)

    def _add_language_step(self) -> None:
        """Step 2: one large button per language; a click translates."""
        self.language_step = QtWidgets.QWidget()
        row = QtWidgets.QHBoxLayout(self.language_step)
        row.setContentsMargins(0, 0, 0, 0)
        row.addWidget(self._step_label(i18n.tr("2. Translate into")))
        self.language_group = QtWidgets.QButtonGroup(self)
        self.language_buttons = {}
        for code in config.LANGUAGES:
            button = self._language_button(code)
            self.language_buttons[code] = button
            row.addWidget(button)
        row.addStretch()
        self.layout_box.addWidget(self.language_step)

    def _language_button(self, code: str) -> QtWidgets.QPushButton:
        """Build one checkable language button that requests a translation."""
        button = QtWidgets.QPushButton(config.language_name(code))
        button.setObjectName("language")
        button.setCheckable(True)
        button.clicked.connect(lambda: self.target_chosen.emit(code))
        self.language_group.addButton(button)
        return button

    def _step_label(self, text: str) -> QtWidgets.QLabel:
        """Label a numbered step in large text."""
        label = QtWidgets.QLabel(text)
        label.setObjectName("step")
        return label

    def _add_texts(self) -> None:
        """Show the song's words and the translation side by side."""
        self.panels = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.panels.setChildrenCollapsible(False)
        self.panels.setHandleWidth(18)
        self.original = text_panel.TextPanel(
            i18n.tr("Song words"), "song-words.txt", True
        )
        self.translated = text_panel.TextPanel(
            i18n.tr("Translation"), "translation.txt"
        )
        self.panels.addWidget(self.original)
        self.panels.addWidget(self.translated)
        self.translated.hide()
        self.layout_box.addWidget(self.panels, 1)

    def _add_status(self) -> None:
        """Show progress, results, and errors in a colored bar."""
        self.activity = activity.Activity()
        self.status = self.activity.status
        self.progress = self.activity.bar
        self.cancel_button = self.activity.cancel
        self.layout_box.addWidget(self.activity)

    def show_transcript(self, ready: bool) -> None:
        """Switch between the welcome screen and the working screen."""
        self.panels.setVisible(ready)
        self.language_step.setVisible(ready)
        self.welcome.setVisible(not ready)
        self.empty_space.setVisible(not ready)
        self.drop.setMinimumHeight(70 if ready else 120)

    def set_song_language(self, code: str) -> None:
        """Hide the song's own language; translating into it does nothing."""
        for language, button in self.language_buttons.items():
            button.setVisible(language != code)

    def select_target(self, code: str) -> None:
        """Mark a language as chosen without starting a translation."""
        self.language_buttons[code].setChecked(True)

    def target(self) -> str:
        """Return the chosen translation language."""
        for code, button in self.language_buttons.items():
            if button.isChecked():
                return code
        return "he"

    def set_busy(self, busy: bool) -> None:
        """Prevent overlapping requests while leaving text readable."""
        for widget in (self.drop, *self.language_buttons.values()):
            widget.setEnabled(not busy)
        self.original.editor.setReadOnly(busy)
        self.activity.set_busy(busy)

    def show_progress(self, message: str, percent: int) -> None:
        """Switch between indeterminate loading and measured progress."""
        self.activity.report(message, percent)

    def show_status(self, message: str, kind: str = "info") -> None:
        """Show a final message: info, success, warning, or error."""
        self.activity.show(message, kind)
