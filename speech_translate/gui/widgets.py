"""Small building blocks shared by the screens: cards, labels, status."""

from PySide6 import QtCore, QtWidgets

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
