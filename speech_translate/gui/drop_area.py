"""A single MP3 drop target that also opens the native file picker."""

import pathlib

from PySide6 import QtCore, QtGui, QtWidgets


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
        """Create the initial empty drop target."""
        super().__init__("Drop an MP3 here\nor click to choose a song")
        self.setAcceptDrops(True)
        self.setMinimumHeight(100)
        self.setObjectName("dropArea")
        self.clicked.connect(self.choose_file)

    def choose_file(self) -> None:
        """Open an MP3-only file picker."""
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            "Choose a song",
            "",
            "MP3 audio (*.mp3)",
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
