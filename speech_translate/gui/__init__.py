"""Desktop entry point; widgets, jobs, and behavior live in small modules."""

import sys

from PySide6 import QtGui, QtWidgets

from speech_translate import config
from speech_translate.gui import theme
from speech_translate.gui.window import Window


def main() -> int:
    """Run the offline desktop application."""
    config.offline_mode()
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QtGui.QFont("Segoe UI", 10))
    app.setStyleSheet(theme.STYLESHEET)
    window = Window()
    window.showFullScreen()
    return app.exec()


__all__ = ["Window", "main"]
