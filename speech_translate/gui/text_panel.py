"""Numbered text panel with native Hebrew direction, copying, and saving."""

import pathlib

from PySide6 import QtCore, QtGui, QtWidgets

from speech_translate import config, i18n
from speech_translate.gui import line_numbers


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
    """One source or translated text, numbered, with copy and save actions."""

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
        self.editor.setFont(QtGui.QFont("Segoe UI", 15))
        self.numbers = line_numbers.LineNumbers(self.editor)
        self._build_layout(title)
        self.editor.textChanged.connect(self._text_changed)

    def _build_layout(self, title: str) -> None:
        """Arrange the title, export buttons, and the numbered editor."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        buttons = QtWidgets.QHBoxLayout()
        self.heading = QtWidgets.QLabel(title)
        self.heading.setObjectName("panelTitle")
        buttons.addWidget(self.heading, 1)
        for label, action in (
            (i18n.tr("Copy"), self.copy_text),
            (i18n.tr("Save…"), self.save_text),
        ):
            button = QtWidgets.QPushButton(label)
            button.clicked.connect(action)
            buttons.addWidget(button)
        layout.addLayout(buttons)
        layout.addWidget(self._numbered_editor())

    def _numbered_editor(self) -> QtWidgets.QWidget:
        """Put line numbers on the side where each line starts."""
        self.text_row = QtWidgets.QWidget()
        row = QtWidgets.QHBoxLayout(self.text_row)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(0)
        row.addWidget(self.numbers)
        row.addWidget(self.editor, 1)
        return self.text_row

    def _text_changed(self) -> None:
        """Maintain paragraph direction and notify the containing window."""
        apply_direction(self.editor, self.language)
        self.changed.emit()

    def set_text(self, text: str, language: str) -> None:
        """Replace the text while preserving logical Unicode order."""
        self.language = language
        name = config.language_name(language) if language else ""
        self.heading.setText(f"{self.title} · {name}" if name else self.title)
        self.text_row.setLayoutDirection(
            QtCore.Qt.LayoutDirection.RightToLeft
            if language == "he"
            else QtCore.Qt.LayoutDirection.LeftToRight
        )
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
            self.notice.emit(i18n.tr("There is no text to save yet."))
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            i18n.tr("Save text"),
            self.filename,
            i18n.tr("Text files (*.txt)"),
        )
        if path:
            self._write_text(path)

    def _write_text(self, path: str) -> None:
        """Write Windows-friendly UTF-8 without changing lyric spacing."""
        try:
            pathlib.Path(path).write_text(self.text(), encoding="utf-8-sig")
            name = pathlib.Path(path).name
            self.notice.emit(i18n.tr("Saved {name}", name=name))
        except OSError as error:
            self.notice.emit(i18n.tr("Could not save: {error}", error=error))
