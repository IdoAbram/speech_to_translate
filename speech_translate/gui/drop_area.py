"""A single MP3 drop target that also opens the native file picker."""

import pathlib

from PySide6 import QtCore, QtGui, QtWidgets

from speech_translate import i18n
from speech_translate.gui import widgets


def dropped_mp3(mime: QtCore.QMimeData) -> str:
    """Accept exactly one local MP3 file, rejecting directories and URLs."""
    urls = mime.urls()
    if len(urls) != 1 or not urls[0].isLocalFile():
        return ""
    path = pathlib.Path(urls[0].toLocalFile())
    return str(path) if path.is_file() and path.suffix.lower() == ".mp3" else ""


class DropArea(QtWidgets.QPushButton):
    """Clickable MP3 selector with native drag-and-drop support."""

    selected = QtCore.Signal(str)

    def __init__(self):
        """Create one large card: icon, title, and how to choose a song."""
        super().__init__()
        self.setAcceptDrops(True)
        self.setObjectName("dropArea")
        self.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.setAccessibleName(i18n.tr("Choose a song"))
        column = QtWidgets.QVBoxLayout(self)
        column.setSpacing(14)
        column.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        for widget in self._contents():
            widget.setAttribute(
                QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents
            )
            column.addWidget(widget, 0, QtCore.Qt.AlignmentFlag.AlignCenter)
        self.clicked.connect(self.choose_file)

    def _contents(self) -> list:
        """Return the icon and the three lines of text, largest first."""
        return [
            widgets.music_icon(96),
            widgets.label(i18n.tr("Choose a song"), "bigTitle"),
            widgets.label(
                i18n.tr("Click here to choose a song file (MP3)"), "hint"
            ),
            widgets.label(i18n.tr("or drag the file here"), "caption"),
        ]

    def choose_file(self) -> None:
        """Open an MP3-only file picker."""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            i18n.tr("Choose a song"),
            "",
            i18n.tr("MP3 songs (*.mp3)"),
        )
        if path:
            self.selected.emit(path)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        """Accept a valid MP3 only when the drop area is enabled."""
        if self.isEnabled() and dropped_mp3(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        """Start transcription after a valid file is dropped."""
        path = dropped_mp3(event.mimeData())
        if self.isEnabled() and path:
            event.acceptProposedAction()
            self.selected.emit(path)
        else:
            event.ignore()
