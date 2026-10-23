"""Settings: online translation and window size, out of grandpa's way."""

from PySide6 import QtCore, QtWidgets

from speech_translate import i18n, settings
from speech_translate.gui import widgets
from speech_translate.translation import groq


class SettingsDialog(QtWidgets.QDialog):
    """Turn better online translation on or off, and switch full screen."""

    key_requested = QtCore.Signal()
    fullscreen_requested = QtCore.Signal()
    online_changed = QtCore.Signal(bool)

    def __init__(self, parent=None):
        """Show the current choices; changes apply immediately."""
        super().__init__(parent)
        self.setWindowTitle(i18n.tr("Settings"))
        self.setMinimumWidth(600)
        column = QtWidgets.QVBoxLayout(self)
        column.setContentsMargins(28, 24, 28, 24)
        column.setSpacing(16)
        column.addWidget(widgets.label(i18n.tr("Settings"), "bigTitle"))
        column.addWidget(self._online_card())
        column.addWidget(self._display_card())
        close = widgets.button(i18n.tr("Close"), "primary")
        close.clicked.connect(self.accept)
        column.addWidget(close)
        self.refresh()

    def _online_card(self) -> QtWidgets.QFrame:
        """The switch, one plain sentence, and the key's state."""
        frame = widgets.card()
        column = QtWidgets.QVBoxLayout(frame)
        column.setContentsMargins(20, 16, 20, 16)
        column.addLayout(self._switch_row())
        explanation = widgets.label(i18n.tr(ONLINE_EXPLANATION), "hint")
        explanation.setWordWrap(True)
        column.addWidget(explanation)
        column.addLayout(self._key_row())
        return frame

    def _switch_row(self) -> QtWidgets.QHBoxLayout:
        """The switch with a plain 'On' or 'Off' beside it."""
        row = QtWidgets.QHBoxLayout()
        self.online = QtWidgets.QCheckBox(
            i18n.tr("Better translation over the internet")
        )
        self.online.setObjectName("switch")
        self.online.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        self.online.toggled.connect(self.online_changed)
        self.online_state = widgets.label()
        row.addWidget(self.online, 1)
        row.addWidget(self.online_state)
        return row

    def _key_row(self) -> QtWidgets.QHBoxLayout:
        """Show whether a key is saved, with a way to change it."""
        row = QtWidgets.QHBoxLayout()
        self.key_state = widgets.label("", "muted")
        change = widgets.button(i18n.tr("Change key…"))
        change.clicked.connect(self.key_requested)
        row.addWidget(self.key_state, 1)
        row.addWidget(change)
        return row

    def _display_card(self) -> QtWidgets.QFrame:
        """Switch between a window and full screen."""
        frame = widgets.card()
        row = QtWidgets.QHBoxLayout(frame)
        row.setContentsMargins(20, 12, 20, 12)
        row.addWidget(widgets.label(i18n.tr("Display"), "settingsHeading"), 1)
        toggle = widgets.button(i18n.tr("Full screen / window"))
        toggle.clicked.connect(self.fullscreen_requested)
        row.addWidget(toggle)
        return frame

    def refresh(self) -> None:
        """Show the saved switch position and whether a key exists."""
        enabled = settings.online_enabled() and bool(groq.api_key())
        with QtCore.QSignalBlocker(self.online):
            self.online.setChecked(enabled)
        self.online_state.setText(i18n.tr("On") if enabled else i18n.tr("Off"))
        self.online_state.setObjectName("stepDone" if enabled else "muted")
        self.online_state.style().polish(self.online_state)
        self.key_state.setText(
            i18n.tr("Groq key: saved ✓")
            if groq.api_key()
            else i18n.tr("No Groq key yet")
        )


ONLINE_EXPLANATION = (
    "When the computer is connected to the internet, the translation "
    "understands slang and expressions much better. Without internet, the "
    "translation is done on this computer, and that always works."
)
