"""Four screens under one top bar; behavior stays in the window module.

start: choose a song · chosen: pick languages · working: progress ·
result: the numbered lyrics and their translation.
"""

from PySide6 import QtCore, QtWidgets

from speech_translate import i18n
from speech_translate.gui import activity, drop_area, pages, widgets

PAGES = ("start", "chosen", "working", "result")


class View(QtWidgets.QWidget):
    """The top bar, the current screen, and a colored status line."""

    fullscreen_requested = QtCore.Signal()
    settings_requested = QtCore.Signal()
    close_requested = QtCore.Signal()

    def __init__(self):
        """Start on the 'choose a song' screen."""
        super().__init__()
        self.setObjectName("workspace")
        column = QtWidgets.QVBoxLayout(self)
        column.setContentsMargins(32, 16, 32, 20)
        column.setSpacing(14)
        column.addLayout(self._top_bar())
        self.pages = QtWidgets.QStackedWidget()
        self._add_pages()
        column.addWidget(self.pages, 1)
        self.status = widgets.StatusBar()
        column.addWidget(self.status)
        self.show_page("start")

    def _top_bar(self) -> QtWidgets.QHBoxLayout:
        """The app's name, then Full screen, Settings, and Exit."""
        row = QtWidgets.QHBoxLayout()
        row.addWidget(widgets.label("SongWords", "appName"), 1)
        for text, signal, name in (
            (i18n.tr("Full screen"), self.fullscreen_requested, ""),
            (i18n.tr("Settings"), self.settings_requested, ""),
            (i18n.tr("Exit"), self.close_requested, "quiet"),
        ):
            action = widgets.button(text, name)
            action.clicked.connect(signal)
            row.addWidget(action)
        return row

    def _add_pages(self) -> None:
        """Create the four screens in their order in PAGES."""
        self.drop = drop_area.DropArea()
        self.chosen = pages.ChosenPage()
        self.activity = activity.Activity()
        self.result = pages.ResultPage()
        self.pages.addWidget(self._middle(self.drop, 720))
        self.pages.addWidget(self.chosen)
        self.pages.addWidget(self._middle(self.activity, 760))
        self.pages.addWidget(self.result)

    @staticmethod
    def _middle(widget: QtWidgets.QWidget, width: int) -> QtWidgets.QWidget:
        """Place a card in the middle of the screen."""
        holder = QtWidgets.QWidget()
        column = QtWidgets.QVBoxLayout(holder)
        column.addStretch()
        column.addWidget(widgets.centered(widget, width))
        column.addStretch()
        return holder

    def show_page(self, name: str) -> None:
        """Switch to one of the four screens."""
        self.pages.setCurrentIndex(PAGES.index(name))

    def page(self) -> str:
        """Return the name of the screen being shown."""
        return PAGES[self.pages.currentIndex()]

    def set_busy(self, busy: bool) -> None:
        """Prevent overlapping work while a model is running."""
        self.activity.set_busy(busy)
        self.drop.setEnabled(not busy)

    def show_progress(self, message: str, percent: int) -> None:
        """Move the progress bar forward."""
        self.activity.report(message, percent)

    def show_status(self, message: str, kind: str = "info") -> None:
        """Show a message in the colored status line."""
        self.status.show_message(message, kind)
