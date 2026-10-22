"""Editable text panel with native Hebrew direction, copying, and saving."""

import pathlib

from PySide6 import QtCore, QtGui, QtWidgets

from speech_translate import config


def apply_direction(editor: QtWidgets.QTextEdit, language: str) -> None:
    """Apply paragraph direction without changing the text or its order."""
    block = paragraph_format(language)
    with QtCore.QSignalBlocker(editor):
        options = editor.document().defaultTextOption()
        options.setTextDirection(block.layoutDirection())
        options.setAlignment(block.alignment())
        editor.document().setDefaultTextOption(options)
        cursor = QtGui.QTextCursor(editor.document())
        cursor.select(QtGui.QTextCursor.SelectionType.Document)
        cursor.mergeBlockFormat(block)


def paragraph_format(language: str) -> QtGui.QTextBlockFormat:
    """Choose native paragraph direction and alignment for a language."""
    direction = QtCore.Qt.LayoutDirection
    alignment = QtCore.Qt.AlignmentFlag
    block = QtGui.QTextBlockFormat()
    block.setLayoutDirection(
        direction.RightToLeft if language == "he" else direction.LeftToRight
    )
    horizontal = (
        alignment.AlignRight if language == "he" else alignment.AlignLeft
    )
    block.setAlignment(horizontal | alignment.AlignAbsolute)
    block.setLineHeight(
        145, QtGui.QTextBlockFormat.LineHeightTypes.ProportionalHeight.value
    )
    return block


class TextPanel(QtWidgets.QWidget):
    """One source or translated text, with a small pair of export actions."""

    changed = QtCore.Signal()
    notice = QtCore.Signal(str)

    def __init__(self, title: str, filename: str, editable: bool = False):
        """Create a text editor and attach its copy/save actions."""
        super().__init__()
        self.setObjectName("textPanel")
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
        self.language = "en"
        self.title = title
        self.filename = filename
        self.editor = QtWidgets.QTextEdit()
        self.editor.setReadOnly(not editable)
        self.editor.setAcceptRichText(False)
        self.editor.setFont(QtGui.QFont("Segoe UI", 13))
        self._build_layout(title)
        self.editor.textChanged.connect(self._text_changed)

    def _build_layout(self, title: str) -> None:
        """Arrange the title, editor, and export buttons."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        buttons = QtWidgets.QHBoxLayout()
        self.heading = QtWidgets.QLabel(title)
        self.heading.setObjectName("panelTitle")
        buttons.addWidget(self.heading, 1)
        for label, action in (
            ("Copy", self.copy_text),
            ("Save text…", self.save_text),
        ):
            button = QtWidgets.QPushButton(label)
            button.clicked.connect(action)
            buttons.addWidget(button)
        layout.addLayout(buttons)
        layout.addWidget(self.editor)

    def _text_changed(self) -> None:
        """Maintain paragraph direction and notify the containing window."""
        apply_direction(self.editor, self.language)
        self.changed.emit()

    def set_text(self, text: str, language: str) -> None:
        """Replace the text while preserving logical Unicode order."""
        self.language = language
        name = config.LANGUAGES.get(language, "")
        self.heading.setText(f"{self.title} · {name}" if name else self.title)
        self.editor.setPlainText(text)

    def text(self) -> str:
        """Return editable text with its explicit lyric line breaks."""
        return self.editor.toPlainText()

    def copy_text(self) -> None:
        """Copy the text with its newlines intact."""
        QtWidgets.QApplication.clipboard().setText(self.text())

    def save_text(self) -> None:
        """Export Unicode text or show a recoverable file-system error."""
        if not self.text().strip():
            self.notice.emit("There is no text to save yet.")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            "Save text",
            self.filename,
            "Text files (*.txt)",
        )
        if path:
            self._write_text(path)

    def _write_text(self, path: str) -> None:
        """Write Windows-friendly UTF-8 without changing lyric spacing."""
        try:
            pathlib.Path(path).write_text(self.text(), encoding="utf-8-sig")
            self.notice.emit(f"Saved {pathlib.Path(path).name}")
        except OSError as error:
            self.notice.emit(f"Could not save: {error}")
