"""Two rows of language buttons: the song's language and the target."""

from PySide6 import QtCore, QtGui, QtWidgets

from speech_translate import config, i18n

# Horizontal padding (2 x 16 px) and border (2 x 2 px), plus breathing room.
SEGMENT_PADDING = 48


def segment(codes, group: QtWidgets.QButtonGroup) -> tuple:
    """Build a pill of exclusive buttons, returning it and its buttons."""
    box = QtWidgets.QWidget()
    box.setObjectName("segment")
    box.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
    row = QtWidgets.QHBoxLayout(box)
    row.setContentsMargins(3, 3, 3, 3)
    row.setSpacing(3)
    buttons = {}
    for code in codes:
        button = QtWidgets.QPushButton(config.language_name(code))
        button.setObjectName("segmentButton")
        button.setCheckable(True)
        button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        button.setMinimumWidth(bold_width(button))
        group.addButton(button)
        row.addWidget(button)
        buttons[code] = button
    return box, buttons


def bold_width(button: QtWidgets.QPushButton) -> int:
    """Room for the label in bold, so a chosen language is never cut off."""
    button.ensurePolished()
    font = QtGui.QFont(button.font())
    font.setBold(True)
    text = QtGui.QFontMetrics(font).horizontalAdvance(button.text())
    return text + SEGMENT_PADDING


class LanguageBar(QtWidgets.QWidget):
    """Choose the song's language and the language to translate into."""

    changed = QtCore.Signal()

    def __init__(self, label_style: str = "settingsHeading"):
        """Default to a Polish song translated into Hebrew."""
        super().__init__()
        row = QtWidgets.QHBoxLayout(self)
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(12)
        self._source_group = QtWidgets.QButtonGroup(self)
        self._target_group = QtWidgets.QButtonGroup(self)
        source, self.source_buttons = segment(
            config.LANGUAGES, self._source_group
        )
        target, self.target_buttons = segment(
            config.LANGUAGES, self._target_group
        )
        self._add(row, i18n.tr("The song is in"), source, label_style)
        row.addWidget(self._arrow())
        self._add(row, i18n.tr("Translate into"), target, label_style)
        self._connect()
        self.set_languages("pl", "he")

    def _add(self, row, text: str, segment_box, label_style: str) -> None:
        """Place a short label before its pill of buttons."""
        label = QtWidgets.QLabel(text)
        label.setObjectName(label_style)
        row.addWidget(label)
        row.addWidget(segment_box)

    def _arrow(self) -> QtWidgets.QLabel:
        """Point from the song's language to the translation language."""
        arrow = QtWidgets.QLabel("←" if i18n.right_to_left() else "→")
        arrow.setObjectName("muted")
        return arrow

    def _connect(self) -> None:
        """Keep the target different from the song's language."""
        for code, button in self.source_buttons.items():
            button.clicked.connect(lambda _, c=code: self._pick_source(c))
        for button in self.target_buttons.values():
            button.clicked.connect(self.changed)

    def _pick_source(self, code: str) -> None:
        """Change the song's language, moving the target if it clashes."""
        target = self.target()
        if target == code:
            target = "en" if code == "he" else "he"
        self.set_languages(code, target)
        self.changed.emit()

    def set_languages(self, source: str, target: str) -> None:
        """Show a source and target, hiding the source among the targets."""
        if target == source:
            target = "en" if source == "he" else "he"
        self.source_buttons[source].setChecked(True)
        for code, button in self.target_buttons.items():
            button.setVisible(code != source)
        self.target_buttons[target].setChecked(True)

    def source(self) -> str:
        """Return the song's language."""
        return self._checked(self.source_buttons)

    def target(self) -> str:
        """Return the translation language."""
        return self._checked(self.target_buttons)

    @staticmethod
    def _checked(buttons: dict) -> str:
        """Return the code of the checked button in a pill."""
        return next(code for code, b in buttons.items() if b.isChecked())
