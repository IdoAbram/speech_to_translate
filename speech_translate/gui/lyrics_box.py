"""A text box for the song's words or their translation.

Both boxes use the same font and line spacing and keep the song's blank
verse lines, so line N of one box sits beside line N of the other. A faint
number marks each non-blank line. In the translation box, hovering
highlights a line and clicking copies it.
"""

from PySide6 import QtCore, QtGui, QtWidgets

from speech_translate.gui import theme, widgets

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

    line_clicked = QtCore.Signal(int)

    def __init__(self, copyable: bool):
        """An editable box, or a read-only box whose lines can be copied."""
        super().__init__()
        self.copyable = copyable
        self.hovered = self.copied = -1
        self.language = "en"
        font = QtGui.QFont("Segoe UI")
        font.setPixelSize(TEXT_SIZE)
        self.setFont(font)
        self.setAcceptRichText(False)
        self.setReadOnly(copyable)
        self.numbers = NumberArea(self)
        self.verticalScrollBar().valueChanged.connect(self.numbers.update)
        self.textChanged.connect(self.numbers.update)
        if copyable:
            self.viewport().setMouseTracking(True)
            self.viewport().setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
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
        self.hovered = self.copied = -1
        self._highlight()
        self.numbers.update()

    def lines(self) -> list:
        """Return every line, blank verse lines included."""
        return self.toPlainText().split("\n")

    def line_number(self, row: int) -> int:
        """Count the non-blank lines up to and including a row."""
        return sum(1 for line in self.lines()[: row + 1] if line.strip())

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

    def mouseMoveEvent(self, event: QtGui.QMouseEvent) -> None:
        """Highlight the line under the mouse in the translation box."""
        if self.copyable:
            row = self.cursorForPosition(event.position().toPoint())
            self._set_hovered(row.blockNumber())
        super().mouseMoveEvent(event)

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        """Stop highlighting when the mouse leaves the box."""
        self._set_hovered(-1)
        super().leaveEvent(event)

    def mousePressEvent(self, event: QtGui.QMouseEvent) -> None:
        """Copy a translated line with one click."""
        if not self.copyable:
            super().mousePressEvent(event)
            return
        block = self.cursorForPosition(event.position().toPoint()).block()
        if block.text().strip():
            self.line_clicked.emit(block.blockNumber())

    def _set_hovered(self, row: int) -> None:
        """Remember the hovered line and repaint the highlights."""
        if row != self.hovered:
            self.hovered = row
            self._highlight()

    def mark_copied(self, row: int) -> None:
        """Show which line was copied last."""
        self.copied = row
        self._highlight()

    def _highlight(self) -> None:
        """Tint the hovered line, then the copied line on top of it."""
        selections = []
        for row, color in (
            (self.hovered, theme.HOVER_ROW),
            (self.copied, theme.COPIED_ROW),
        ):
            block = self.document().findBlockByNumber(row)
            if row >= 0 and block.isValid() and block.text().strip():
                selections.append(line_tint(block, color))
        self.setExtraSelections(selections)


def line_tint(block: QtGui.QTextBlock, color: str):
    """Tint a whole line, edge to edge, without selecting its text."""
    selection = QtWidgets.QTextEdit.ExtraSelection()
    selection.format.setBackground(QtGui.QColor(color))
    selection.format.setProperty(
        QtGui.QTextFormat.Property.FullWidthSelection, True
    )
    selection.cursor = QtGui.QTextCursor(block)
    return selection


class LyricsBox(QtWidgets.QFrame):
    """A card with a title, a short hint, buttons, and the text itself."""

    def __init__(self, hint: str, copyable: bool, buttons: list):
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
        self.editor = LyricsEditor(copyable)
        column.addWidget(self.editor, 1)
