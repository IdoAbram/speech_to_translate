"""Simple desktop layout; application behavior stays in the window module."""

from PySide6 import QtCore, QtGui, QtWidgets

from speech_translate import config
from speech_translate.gui import activity, drop_area, text_panel


def language_picker(default: str) -> QtWidgets.QComboBox:
    """Build a language selector with stable language-code item data."""
    picker = QtWidgets.QComboBox()
    if default is None:
        picker.addItem("Automatic", None)
    for code, name in config.LANGUAGES.items():
        picker.addItem(name, code)
    picker.setCurrentIndex(picker.findData(default))
    return picker


class View(QtWidgets.QWidget):
    """Drop target, language controls, two text panels, and loading status."""

    fullscreen_requested = QtCore.Signal()
    close_requested = QtCore.Signal()

    def __init__(self):
        """Create an uncluttered initial screen with translation hidden."""
        super().__init__()
        self.setObjectName("workspace")
        self.layout_box = QtWidgets.QVBoxLayout(self)
        self.layout_box.setContentsMargins(36, 24, 36, 24)
        self.layout_box.setSpacing(18)
        self.layout_box.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self._add_header()
        self._add_input()
        self._add_translation_controls()
        self._add_texts()
        self._add_status()
        self.empty_space = QtWidgets.QWidget()
        self.layout_box.addWidget(self.empty_space, 1)

    def show_transcript(self, ready: bool) -> None:
        """Use spare space for the empty screen or the transcript panels."""
        self.panels.setVisible(ready)
        self.translation_controls.setVisible(ready)
        self.empty_space.setVisible(not ready)

    def _add_header(self) -> None:
        """Explain the workflow in one short sentence."""
        self._add_window_controls()
        title = QtWidgets.QLabel("Every song has a story.")
        title.setObjectName("hero")
        title.setFont(QtGui.QFont("Segoe UI", 30, QtGui.QFont.Weight.DemiBold))
        self.layout_box.addWidget(title)
        subtitle = QtWidgets.QLabel(
            "Drop your MP3. Find the words. Read them in another language."
        )
        subtitle.setObjectName("subtitle")
        self.layout_box.addWidget(subtitle)

    def _add_window_controls(self) -> None:
        """Keep exit and fullscreen controls visible without a title bar."""
        row = QtWidgets.QHBoxLayout()
        badge = QtWidgets.QLabel("SONGWORDS  /  OFFLINE")
        badge.setObjectName("eyebrow")
        row.addWidget(badge, 1)
        for label, signal in (
            ("Window / Fullscreen", self.fullscreen_requested),
            ("Exit", self.close_requested),
        ):
            button = QtWidgets.QPushButton(label)
            button.clicked.connect(signal.emit)
            row.addWidget(button)
        self.layout_box.addLayout(row)

    def _add_input(self) -> None:
        """Use automatic detection with an optional language override."""
        row = QtWidgets.QHBoxLayout()
        self.source = language_picker(None)
        self.online = QtWidgets.QPushButton("Online translation: off")
        settings = QtWidgets.QPushButton("Language settings")
        settings.setCheckable(True)
        settings.toggled.connect(self.source.setVisible)
        self.source.hide()
        self.detected = QtWidgets.QLabel("English · Hebrew · Polish")
        row.addWidget(self.detected)
        row.addStretch()
        row.addWidget(self.online)
        row.addWidget(settings)
        row.addWidget(self.source)
        self.layout_box.addLayout(row)
        self.drop = drop_area.DropArea()
        self.layout_box.addWidget(self.drop)

    def _add_translation_controls(self) -> None:
        """Reveal the target language and Translate button after recognition."""
        self.translation_controls = QtWidgets.QWidget()
        row = QtWidgets.QHBoxLayout(self.translation_controls)
        row.setContentsMargins(0, 0, 0, 0)
        self.target = language_picker("he")
        self.translate_button = QtWidgets.QPushButton("Translate")
        self.translate_button.setObjectName("primary")
        row.addWidget(QtWidgets.QLabel("Translate into"))
        row.addWidget(self.target)
        row.addWidget(self.translate_button)
        row.addStretch()
        self.translation_controls.hide()
        self.layout_box.addWidget(self.translation_controls)

    def _add_texts(self) -> None:
        """Keep the transcript visible when a translation is displayed."""
        self.panels = QtWidgets.QSplitter(QtCore.Qt.Orientation.Horizontal)
        self.panels.setChildrenCollapsible(False)
        self.panels.setHandleWidth(18)
        self.original = text_panel.TextPanel(
            "Transcript", "transcript.txt", True
        )
        self.translated = text_panel.TextPanel("Translation", "translation.txt")
        self.panels.addWidget(self.original)
        self.panels.addWidget(self.translated)
        self.translated.hide()
        self.panels.hide()
        self.layout_box.addWidget(self.panels, 1)

    def _add_status(self) -> None:
        """Display loading progress, cancellation, and actionable errors."""
        self.activity = activity.Activity()
        self.status = self.activity.status
        self.progress = self.activity.bar
        self.cancel_button = self.activity.cancel
        self.layout_box.addWidget(self.activity)

    def set_busy(self, busy: bool) -> None:
        """Prevent overlapping requests while leaving text readable."""
        for widget in (
            self.source,
            self.target,
            self.drop,
            self.online,
            self.translate_button,
        ):
            widget.setEnabled(not busy)
        self.original.editor.setReadOnly(busy)
        self.activity.set_busy(busy)

    def show_progress(self, message: str, percent: int) -> None:
        """Switch between indeterminate loading and measured progress."""
        self.activity.report(message, percent)
