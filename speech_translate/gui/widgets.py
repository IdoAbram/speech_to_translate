"""Small building blocks shared by the screens: cards, labels, status."""

from PySide6 import QtCore, QtWidgets

from speech_translate import i18n

KINDS = ("info", "success", "warning", "error")


def card() -> QtWidgets.QFrame:
    """Return a white rounded card for one group of content."""
    frame = QtWidgets.QFrame()
    frame.setObjectName("card")
    return frame


def label(text: str = "", name: str = "") -> QtWidgets.QLabel:
    """Return a plain-text label styled by its object name."""
    widget = QtWidgets.QLabel(text)
    widget.setTextFormat(QtCore.Qt.TextFormat.PlainText)
    if name:
        widget.setObjectName(name)
    return widget


def leading() -> QtCore.Qt.AlignmentFlag:
    """Align to where lines start: right in Hebrew, left otherwise.

    Qt aligns a label by its own text, so a Latin file name would otherwise
    jump to the left edge of a Hebrew screen.
    """
    flags = QtCore.Qt.AlignmentFlag
    side = flags.AlignRight if i18n.right_to_left() else flags.AlignLeft
    return side | flags.AlignAbsolute | flags.AlignVCenter


class SongLabel(QtWidgets.QLabel):
    """A bold song name that shortens its middle only when it must."""

    def __init__(self):
        """Start empty, aligned to where the reader's eye starts."""
        super().__init__()
        self.setObjectName("songName")
        self.setTextFormat(QtCore.Qt.TextFormat.PlainText)
        self.setAlignment(leading())
        self.setSizePolicy(
            QtWidgets.QSizePolicy.Policy.Ignored,
            QtWidgets.QSizePolicy.Policy.Preferred,
        )
        self.full_name = ""

    def set_song(self, name: str) -> None:
        """Show a song's name; the tooltip always has all of it."""
        self.full_name = name
        self.setToolTip(name)
        self._fit()

    def resizeEvent(self, event) -> None:
        """Fit the name again whenever the window changes size."""
        super().resizeEvent(event)
        self._fit()

    def _fit(self) -> None:
        """Shorten the middle of the name if it is wider than the label."""
        self.ensurePolished()
        elide = QtCore.Qt.TextElideMode.ElideMiddle
        width = max(self.width(), 1)
        self.setText(
            self.fontMetrics().elidedText(self.full_name, elide, width)
        )


def divider() -> QtWidgets.QFrame:
    """A thin line between two groups inside a card."""
    line = QtWidgets.QFrame()
    line.setObjectName("divider")
    line.setFixedHeight(1)
    return line


def music_icon(size: int = 64) -> QtWidgets.QLabel:
    """Return the soft square music note used beside a song."""
    icon = label("♫", "musicIcon")
    icon.setFixedSize(size, size)
    icon.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
    return icon


def button(text: str, name: str = "") -> QtWidgets.QPushButton:
    """Return a button with a pointing-hand cursor and optional style."""
    widget = QtWidgets.QPushButton(text)
    widget.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
    if name:
        widget.setObjectName(name)
    return widget


def centered(widget: QtWidgets.QWidget, width: int) -> QtWidgets.QWidget:
    """Center a widget of limited width in the remaining space."""
    holder = QtWidgets.QWidget()
    row = QtWidgets.QHBoxLayout(holder)
    row.setContentsMargins(0, 0, 0, 0)
    widget.setMaximumWidth(width)
    row.addWidget(widget)
    return holder


class StatusBar(QtWidgets.QLabel):
    """A colored line at the bottom: info, success, warning, or error."""

    def __init__(self):
        """Start hidden until there is something to say."""
        super().__init__()
        self.setObjectName("status")
        self.setTextFormat(QtCore.Qt.TextFormat.PlainText)
        self.setWordWrap(True)
        self.hide()

    def show_message(self, message: str, kind: str = "info") -> None:
        """Show a message colored by its kind."""
        if kind not in KINDS:
            raise ValueError(f"Unknown status kind: {kind}")
        self.setText(message)
        self.setProperty("kind", kind)
        self.style().unpolish(self)
        self.style().polish(self)
        self.setVisible(bool(message))

    def clear_message(self) -> None:
        """Hide the bar."""
        self.show_message("", "info")
