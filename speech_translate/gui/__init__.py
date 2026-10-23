"""Desktop entry point; widgets, jobs, and behavior live in small modules."""

import sys

from PySide6 import QtCore, QtGui, QtWidgets

from speech_translate import config, i18n
from speech_translate.gui import theme
from speech_translate.gui.window import Window


def main() -> int:
    """Run the desktop application in Hebrew, laid out right to left."""
    config.offline_mode()
    i18n.set_language("he")
    app = QtWidgets.QApplication(sys.argv)
    app.setLayoutDirection(QtCore.Qt.LayoutDirection.RightToLeft)
    app.setStyle("Fusion")
    app.setFont(QtGui.QFont("Segoe UI", 10))
    app.setStyleSheet(theme.STYLESHEET)
    window = Window()
    window.showFullScreen()
    return app.exec()


__all__ = ["Window", "main"]
