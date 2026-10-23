"""The song and its translation, one numbered row per line.

Hovering a row highlights it; clicking copies that line. Blank rows keep
the song's verse breaks and are not numbered, so line N of the song is
always beside line N of the translation.
"""

from PySide6 import QtCore, QtGui, QtWidgets

from speech_translate import i18n
from speech_translate.gui import theme

NUMBER, SOURCE, TRANSLATION, HINT = range(4)
BLANK_ROW_HEIGHT = 20
SIZES = {NUMBER: 17, SOURCE: 21, TRANSLATION: 23, HINT: 15}
WIDTHS = {NUMBER: 70, HINT: 150}


def cell_font(column: int) -> QtGui.QFont:
    """Larger text for the translation, bold for numbers and hints."""
    font = QtGui.QFont("Segoe UI")
    font.setPixelSize(SIZES[column])
    font.setBold(column in (NUMBER, HINT))
    return font


class LyricsTable(QtWidgets.QTableWidget):
    """Line N of the song beside line N of its translation."""

    line_clicked = QtCore.Signal(int)
    edited = QtCore.Signal()

    def __init__(self):
        """Create an empty table; double-click a song line to fix it."""
        super().__init__(0, 4)
        self.hovered = -1
        self.copied = -1
        self._setup_view()
        self.cellEntered.connect(lambda row, _: self._set_hovered(row))
        self.cellClicked.connect(self._click)
        self.itemChanged.connect(self._item_changed)

    def _setup_view(self) -> None:
        """No grid or selection; text wraps; the cursor invites a click."""
        self.setMouseTracking(True)
        self.setShowGrid(False)
        self.setWordWrap(True)
        self.setSelectionMode(self.SelectionMode.NoSelection)
        self.setEditTriggers(
            self.EditTrigger.DoubleClicked | self.EditTrigger.EditKeyPressed
        )
        self.verticalHeader().hide()
        self.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.viewport().setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self._size_columns()

    def _size_columns(self) -> None:
        """Fixed number and hint columns; the two texts share the rest."""
        header = self.horizontalHeader()
        mode = QtWidgets.QHeaderView.ResizeMode
        for column in range(self.columnCount()):
            fixed = column in WIDTHS
            header.setSectionResizeMode(
                column, mode.Fixed if fixed else mode.Stretch
            )
            if fixed:
                self.setColumnWidth(column, WIDTHS[column])

    def set_headers(self, source_name: str, target_name: str) -> None:
        """Name both languages above their columns."""
        self.setHorizontalHeaderLabels(
            [
                i18n.tr("Line"),
                i18n.tr("Song words · {language}", language=source_name),
                i18n.tr("Translation · {language}", language=target_name),
                "",
            ]
        )

    def set_lines(self, source_lines: list, translated=None) -> None:
        """Fill one row per source line, with its translation if known."""
        translated = translated or [""] * len(source_lines)
        with QtCore.QSignalBlocker(self):
            self.setRowCount(len(source_lines))
            number = 0
            for row, text in enumerate(source_lines):
                number += bool(text.strip())
                self._fill_row(row, text, translated[row], number)
        self.hovered = self.copied = -1
        self._fit_rows()

    def _fill_row(self, row: int, text: str, translation: str, number: int):
        """Write one row; blank rows only keep a verse break."""
        blank = not text.strip()
        values = ("" if blank else str(number), text, translation, "")
        for column, value in enumerate(values):
            self.setItem(row, column, self._item(value, column, blank))

    def _item(self, value: str, column: int, blank: bool):
        """Make one cell; only non-blank song lines can be edited."""
        item = QtWidgets.QTableWidgetItem(value)
        flags = QtCore.Qt.ItemFlag.ItemIsEnabled
        if column == SOURCE and not blank:
            flags |= QtCore.Qt.ItemFlag.ItemIsEditable
        item.setFlags(flags)
        item.setFont(cell_font(column))
        if column == NUMBER:
            item.setTextAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
            item.setForeground(QtGui.QColor("#8C8A82"))
        if column == HINT:
            item.setForeground(QtGui.QColor(theme.ACCENT_DARK))
        return item

    def _fit_rows(self) -> None:
        """Size rows to their text, keeping verse breaks thin."""
        self.resizeRowsToContents()
        for row in range(self.rowCount()):
            if self.is_blank(row):
                self.setRowHeight(row, BLANK_ROW_HEIGHT)

    def is_blank(self, row: int) -> bool:
        """Return whether a row is a verse break rather than a line."""
        item = self.item(row, SOURCE)
        return item is None or not item.text().strip()

    def line_number(self, row: int) -> int:
        """Return the number shown beside a line."""
        return int(self.item(row, NUMBER).text())

    def source_lines(self) -> list:
        """Return the song's lines, including edits and verse breaks."""
        return [self.item(r, SOURCE).text() for r in range(self.rowCount())]

    def translated_lines(self) -> list:
        """Return the translation's lines, empty where none exists."""
        rows = range(self.rowCount())
        return [self.item(r, TRANSLATION).text() for r in rows]

    def clear_translation(self) -> None:
        """Remove translations that no longer match edited words."""
        with QtCore.QSignalBlocker(self):
            for row in range(self.rowCount()):
                self.item(row, TRANSLATION).setText("")
        self.copied = -1
        self._fit_rows()

    def mark_copied(self, row: int) -> None:
        """Show which line was copied last."""
        previous, self.copied = self.copied, row
        self._paint(previous)
        self._paint(row)

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        """Stop highlighting when the mouse leaves the lyrics."""
        self._set_hovered(-1)
        super().leaveEvent(event)

    def _set_hovered(self, row: int) -> None:
        """Highlight the row under the mouse."""
        if row != self.hovered:
            previous, self.hovered = self.hovered, row
            self._paint(previous)
            self._paint(row)

    def _paint(self, row: int) -> None:
        """Color a row and its hint: copied, hovered, or plain."""
        if not 0 <= row < self.rowCount() or self.is_blank(row):
            return
        copied, hovered = row == self.copied, row == self.hovered
        color = theme.COPIED_ROW if copied else theme.HOVER_ROW
        background = QtGui.QColor(color if copied or hovered else "#FFFFFF")
        hint = i18n.tr("Copied ✓") if copied else ""
        hint = hint or (i18n.tr("Click to copy") if hovered else "")
        with QtCore.QSignalBlocker(self):
            for column in range(self.columnCount()):
                self.item(row, column).setBackground(background)
            self.item(row, HINT).setText(hint)

    def _click(self, row: int, column: int) -> None:
        """Ask the window to copy a line; verse breaks are ignored."""
        if not self.is_blank(row):
            self.line_clicked.emit(row)

    def _item_changed(self, item: QtWidgets.QTableWidgetItem) -> None:
        """Report a corrected song line."""
        if item.column() == SOURCE:
            self.edited.emit()
