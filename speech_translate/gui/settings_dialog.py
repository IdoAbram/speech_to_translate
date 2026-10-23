"""Rarely needed options, kept off the main screen."""

from PySide6 import QtCore, QtWidgets

from speech_translate import config, i18n


class SettingsDialog(QtWidgets.QDialog):
    """Song language override, online translation, and window size."""

    key_requested = QtCore.Signal()
    fullscreen_requested = QtCore.Signal()

    def __init__(self, source: str | None, online: bool, parent=None):
        """Show the current choices; the window applies them on close."""
        super().__init__(parent)
        self.setWindowTitle(i18n.tr("Settings"))
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(12)
        self._add_language(layout, source)
        self._add_online(layout)
        self.show_online(online)
        fullscreen = QtWidgets.QPushButton(i18n.tr("Window / full screen"))
        fullscreen.clicked.connect(self.fullscreen_requested)
        layout.addWidget(fullscreen)
        close = QtWidgets.QPushButton(i18n.tr("Close"))
        close.setObjectName("primary")
        close.clicked.connect(self.accept)
        layout.addWidget(close)

    def _add_language(self, layout, source: str | None) -> None:
        """Let the user correct a wrongly detected song language."""
        layout.addWidget(self._heading(i18n.tr("Song language")))
        self.language = QtWidgets.QComboBox()
        self.language.addItem(i18n.tr("Detect automatically"), None)
        for code in config.LANGUAGES:
            self.language.addItem(config.language_name(code), code)
        self.language.setCurrentIndex(self.language.findData(source))
        layout.addWidget(self.language)
        layout.addWidget(
            self._hint(
                i18n.tr(
                    "If the words came out in the wrong language, choose the "
                    "song's language here. The song is read again."
                )
            )
        )

    def _add_online(self, layout) -> None:
        """Show whether lyrics are translated online, and how to change it."""
        layout.addWidget(self._heading(i18n.tr("Online translation")))
        row = QtWidgets.QHBoxLayout()
        self.online_state = QtWidgets.QLabel()
        change = QtWidgets.QPushButton(i18n.tr("Change…"))
        change.clicked.connect(self.key_requested)
        row.addWidget(self.online_state, 1)
        row.addWidget(change)
        layout.addLayout(row)

    def _heading(self, text: str) -> QtWidgets.QLabel:
        """Label one group of settings."""
        label = QtWidgets.QLabel(text)
        label.setObjectName("settingsHeading")
        return label

    def _hint(self, text: str) -> QtWidgets.QLabel:
        """Explain a setting in a short, wrapped sentence."""
        label = QtWidgets.QLabel(text)
        label.setObjectName("hint")
        label.setWordWrap(True)
        return label

    def show_online(self, online: bool) -> None:
        """Describe the current translation mode in plain words."""
        self.online_state.setText(
            i18n.tr("On: better translation over the internet")
            if online
            else i18n.tr("Off: translation on this computer only")
        )

    def source(self) -> str | None:
        """Return the chosen song language, or None to detect it."""
        return self.language.currentData()
