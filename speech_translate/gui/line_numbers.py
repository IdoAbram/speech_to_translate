"""Line numbers beside lyrics, so line N of both texts is easy to match."""

from PySide6 import QtCore, QtGui, QtWidgets

NUMBER_COLOR = "#7f93ad"
WIDTH = 44


class LineNumbers(QtWidgets.QWidget):
    """Number each non-empty line; blank stanza lines stay unnumbered.

    Both texts keep the same blank lines, so the same number always marks
    a source line and its translation.
    """

    def __init__(self, editor: QtWidgets.QTextEdit):
        """Follow the editor's text and scrolling."""
        super().__init__()
        self.editor = editor
        self.setFixedWidth(WIDTH)
        editor.textChanged.connect(self.update)
        editor.verticalScrollBar().valueChanged.connect(self.update)
        layout = editor.document().documentLayout()
        layout.documentSizeChanged.connect(self.update)

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        """Draw the number of each visible lyric line at its first row."""
        painter = QtGui.QPainter(self)
        painter.setFont(self.editor.font())
        painter.setPen(QtGui.QColor(NUMBER_COLOR))
        for number, top, height in self.visible_lines():
            area = QtCore.QRect(6, top, self.width() - 12, height)
            painter.drawText(area, self.alignment(), str(number))

    def alignment(self) -> QtCore.Qt.AlignmentFlag:
        """Keep numbers next to the text, whichever side it starts on."""
        flags = QtCore.Qt.AlignmentFlag
        right_to_left = QtCore.Qt.LayoutDirection.RightToLeft
        side = (
            flags.AlignLeft
            if self.layoutDirection() == right_to_left
            else flags.AlignRight
        )
        return side | flags.AlignAbsolute | flags.AlignVCenter

    def visible_lines(self):
        """Yield the number, top, and height of each non-empty line shown."""
        number = 0
        block = self.editor.document().firstBlock()
        while block.isValid():
            if block.text().strip():
                number += 1
                top, height = self.position(block)
                if top > self.height():
                    return
                if top + height >= 0:
                    yield number, top, height
            block = block.next()

    def position(self, block: QtGui.QTextBlock) -> tuple[int, int]:
        """Map a block's first row from the editor into this widget."""
        layout = self.editor.document().documentLayout()
        rect = layout.blockBoundingRect(block)
        first_row = block.layout().lineAt(0)
        row_top = rect.top() + (first_row.y() if first_row.isValid() else 0)
        offset = self.editor.verticalScrollBar().value()
        viewport = self.editor.viewport()
        point = QtCore.QPoint(0, int(row_top - offset))
        top = self.mapFrom(self.window(), viewport.mapTo(self.window(), point))
        height = int(first_row.height()) if first_row.isValid() else 0
        return top.y(), height or int(rect.height())
