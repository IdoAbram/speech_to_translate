"""A text box for the song's words or their translation.

Both boxes use the same font and line spacing and keep the song's blank
verse lines, so line N of one box sits beside line N of the other. A faint
number marks each non-blank line. Both boxes can be edited.
"""

from PySide6 import QtCore, QtGui, QtWidgets

from speech_translate.gui import widgets

NUMBER_WIDTH = 40
TEXT_SIZE = 22
LINE_SPACING = 160


class NumberArea(QtWidgets.QWidget):
    """The gutter beside the text; the editor paints its numbers."""

    def __init__(self, editor: "LyricsEditor"):
        """Belong to the editor so it moves and scrolls with it."""
        super().__init__(editor)
        self.editor = editor

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        """Let the editor draw the visible line numbers."""
        self.editor.paint_numbers()


class LyricsEditor(QtWidgets.QTextEdit):
    """Plain lyrics with faint line numbers on the side lines start on."""

    def __init__(self):
        """An editable box laid out for the song's language."""
        super().__init__()
        self.language = "en"
        font = QtGui.QFont("Segoe UI")
        font.setPixelSize(TEXT_SIZE)
        self.setFont(font)
        self.setAcceptRichText(False)
        self.numbers = NumberArea(self)
        self.verticalScrollBar().valueChanged.connect(self.numbers.update)
        self.textChanged.connect(self.numbers.update)
        self.set_language("en")

    def set_language(self, code: str) -> None:
        """Lay out Hebrew right to left and other languages left to right."""
        self.language = code
        self.setLayoutDirection(self._direction())
        self._format_lines()
        self._place_numbers()

    def _direction(self) -> QtCore.Qt.LayoutDirection:
        """Return the reading direction of the box's language."""
        direction = QtCore.Qt.LayoutDirection
        rtl = self.language == "he"
        return direction.RightToLeft if rtl else direction.LeftToRight

    def _format_lines(self) -> None:
        """Apply direction, alignment, and roomy spacing to every line."""
        side = QtCore.Qt.AlignmentFlag
        edge = side.AlignRight if self.language == "he" else side.AlignLeft
        block = QtGui.QTextBlockFormat()
        block.setLayoutDirection(self._direction())
        block.setAlignment(edge | side.AlignAbsolute)
        proportional = QtGui.QTextBlockFormat.LineHeightTypes.ProportionalHeight
        block.setLineHeight(LINE_SPACING, proportional.value)
        option = self.document().defaultTextOption()
        option.setTextDirection(self._direction())
        option.setAlignment(edge | side.AlignAbsolute)
        with QtCore.QSignalBlocker(self):
            self.document().setDefaultTextOption(option)
            cursor = QtGui.QTextCursor(self.document())
            cursor.select(QtGui.QTextCursor.SelectionType.Document)
            cursor.mergeBlockFormat(block)

    def set_lines(self, lines: list) -> None:
        """Show lines without reporting them as an edit."""
        with QtCore.QSignalBlocker(self):
            self.setPlainText("\n".join(lines))
        self._format_lines()
        self.numbers.update()

    def lines(self) -> list:
        """Return every line, blank verse lines included."""
        return self.toPlainText().split("\n")

    def _place_numbers(self) -> None:
        """Reserve the gutter on the side where lines start."""
        rtl = self._direction() == QtCore.Qt.LayoutDirection.RightToLeft
        left, right = (0, NUMBER_WIDTH) if rtl else (NUMBER_WIDTH, 0)
        self.setViewportMargins(left, 0, right, 0)
        rect = self.contentsRect()
        x = rect.right() - NUMBER_WIDTH + 1 if rtl else rect.left()
        self.numbers.setGeometry(x, rect.top(), NUMBER_WIDTH, rect.height())

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        """Keep the gutter beside the text when the box is resized."""
        super().resizeEvent(event)
        self._place_numbers()

    def paint_numbers(self) -> None:
        """Draw a faint number beside each visible non-blank line."""
        painter = QtGui.QPainter(self.numbers)
        painter.setPen(QtGui.QColor("#B9B6AC"))
        small = QtGui.QFont(self.font())
        small.setPixelSize(15)
        painter.setFont(small)
        center = QtCore.Qt.AlignmentFlag.AlignCenter
        for number, top, height in self._numbered_lines():
            box = QtCore.QRect(4, top, NUMBER_WIDTH - 8, height)
            painter.drawText(box, center, number)

    def _numbered_lines(self):
        """Yield the label, top, and height of every non-blank line."""
        layout = self.document().documentLayout()
        offset = self.verticalScrollBar().value()
        number = 0
        block = self.document().firstBlock()
        while block.isValid():
            first = block.layout().lineAt(0)
            if block.text().strip() and first.isValid():
                number += 1
                top = layout.blockBoundingRect(block).top() + first.y()
                yield str(number), round(top - offset), round(first.height())
            block = block.next()


class LyricsBox(QtWidgets.QFrame):
    """A card with a title, a short hint, buttons, and the text itself."""

    def __init__(self, hint: str, buttons: list):
        """Arrange the title row, the hint, and the editor."""
        super().__init__()
        self.setObjectName("card")
        column = QtWidgets.QVBoxLayout(self)
        column.setContentsMargins(18, 14, 18, 14)
        column.setSpacing(8)
        row = QtWidgets.QHBoxLayout()
        self.title = widgets.label("", "settingsHeading")
        row.addWidget(self.title, 1)
        for button in buttons:
            row.addWidget(button)
        column.addLayout(row)
        column.addWidget(widgets.label(hint, "caption"))
        self.editor = LyricsEditor()
        column.addWidget(self.editor, 1)
