"""A small dialog for turning Groq online translation on or off."""

from PySide6 import QtWidgets

from speech_translate import config
from speech_translate.translation import groq

KEYS_URL = "https://console.groq.com/keys"


class KeyDialog(QtWidgets.QDialog):
    """Paste, save, or remove the Groq key for this Windows user."""

    def __init__(self, parent=None):
        """Show the explanation, a hidden key field, and the actions."""
        super().__init__(parent)
        self.setWindowTitle("Online translation")
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(14)
        layout.addWidget(self._explanation())
        self.field = QtWidgets.QLineEdit()
        self.field.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        self.field.setPlaceholderText("Paste the Groq key (starts with gsk_)")
        layout.addWidget(self.field)
        self.message = QtWidgets.QLabel()
        layout.addWidget(self.message)
        layout.addLayout(self._buttons())

    def _explanation(self) -> QtWidgets.QLabel:
        """Say what Groq does, where to get a key, and what is sent."""
        label = QtWidgets.QLabel(
            "Groq translates slang and idioms much better than the offline "
            "model. Get a free key (no card needed) at "
            f'<a href="{KEYS_URL}" style="color:#77ddc6">console.groq.com'
            "</a> and paste it below. When you translate, the lyrics are "
            "sent to Groq. Without internet the offline model is used."
        )
        label.setWordWrap(True)
        label.setOpenExternalLinks(True)
        return label

    def _buttons(self) -> QtWidgets.QHBoxLayout:
        """Offer turning online translation off, cancelling, and saving."""
        row = QtWidgets.QHBoxLayout()
        self.remove_button = QtWidgets.QPushButton("Turn off")
        self.remove_button.setEnabled(groq.user_key_path().is_file())
        self.remove_button.clicked.connect(self.remove)
        cancel = QtWidgets.QPushButton("Cancel")
        cancel.clicked.connect(self.reject)
        save = QtWidgets.QPushButton("Save")
        save.setObjectName("primary")
        save.setDefault(True)
        save.clicked.connect(self.save)
        row.addWidget(self.remove_button)
        row.addStretch()
        row.addWidget(cancel)
        row.addWidget(save)
        return row

    def save(self) -> None:
        """Store the pasted key, explaining a problem instead of closing."""
        try:
            groq.save_key(self.field.text())
        except (config.AppError, OSError) as error:
            self.message.setText(str(error))
            return
        self.accept()

    def remove(self) -> None:
        """Forget the saved key so translation stays on this computer."""
        try:
            groq.remove_key()
        except OSError as error:
            self.message.setText(f"The key could not be removed: {error}")
            return
        self.accept()
