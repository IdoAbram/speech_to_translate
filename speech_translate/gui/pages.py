"""The 'song chosen' screen and the 'translated' screen."""

from PySide6 import QtCore, QtWidgets

from speech_translate import i18n
from speech_translate.gui import language_bar, lyrics_table, widgets


def centered_row(*items) -> QtWidgets.QHBoxLayout:
    """Center widgets in a row."""
    row = QtWidgets.QHBoxLayout()
    row.addStretch()
    for item in items:
        row.addWidget(item)
    row.addStretch()
    return row


class ChosenPage(QtWidgets.QWidget):
    """Screen 2: the chosen song, its languages, and a big Translate."""

    other_song = QtCore.Signal()
    translate_requested = QtCore.Signal()

    def __init__(self):
        """Center one card in the window."""
        super().__init__()
        column = QtWidgets.QVBoxLayout(self)
        column.addStretch()
        column.addWidget(widgets.centered(self._card(), 980))
        column.addStretch()

    def _card(self) -> QtWidgets.QFrame:
        """Song on top, languages in the middle, Translate at the bottom."""
        frame = widgets.card()
        column = QtWidgets.QVBoxLayout(frame)
        column.setContentsMargins(32, 28, 32, 28)
        column.setSpacing(24)
        column.addLayout(self._song_row())
        self.languages = language_bar.LanguageBar()
        column.addLayout(centered_row(self.languages))
        self.translate = widgets.button(i18n.tr("Translate"), "bigPrimary")
        self.translate.clicked.connect(self.translate_requested)
        column.addLayout(centered_row(self.translate))
        return frame

    def _song_row(self) -> QtWidgets.QHBoxLayout:
        """Show the song's name and a way to pick a different one."""
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(16)
        names = QtWidgets.QVBoxLayout()
        names.addWidget(widgets.label(i18n.tr("The chosen song"), "caption"))
        self.song = widgets.label("", "songName")
        names.addWidget(self.song)
        other = widgets.button(i18n.tr("Another song"))
        other.clicked.connect(self.other_song)
        row.addWidget(widgets.music_icon(64))
        row.addLayout(names, 1)
        row.addWidget(other)
        return row

    def set_song(self, name: str) -> None:
        """Name the chosen song."""
        self.song.setText(name)


class ResultPage(QtWidgets.QWidget):
    """Screen 4: compact controls on top, the numbered lyrics below."""

    new_song = QtCore.Signal()
    translate_requested = QtCore.Signal()
    copy_all = QtCore.Signal()
    save = QtCore.Signal()

    def __init__(self):
        """Give the lyrics most of the window."""
        super().__init__()
        column = QtWidgets.QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(14)
        column.addWidget(self._top_card())
        column.addWidget(self._lyrics_card(), 1)

    def _top_card(self) -> QtWidgets.QFrame:
        """The song with 'New song', then the languages and Translate."""
        frame = widgets.card()
        column = QtWidgets.QVBoxLayout(frame)
        column.setContentsMargins(18, 12, 18, 12)
        column.setSpacing(12)
        column.addLayout(self._song_row())
        row = QtWidgets.QHBoxLayout()
        self.languages = language_bar.LanguageBar("muted")
        self.translate = widgets.button(i18n.tr("Translate"), "primary")
        self.translate.clicked.connect(self.translate_requested)
        row.addWidget(self.languages)
        row.addWidget(self.translate)
        row.addStretch()
        column.addLayout(row)
        return frame

    def _song_row(self) -> QtWidgets.QHBoxLayout:
        """Name the song and offer a clear way to start a new one."""
        row = QtWidgets.QHBoxLayout()
        self.song = widgets.label("", "songName")
        new_song = widgets.button(i18n.tr("+ New song"), "newSong")
        new_song.clicked.connect(self.new_song)
        row.addWidget(widgets.music_icon(44))
        row.addWidget(self.song, 1)
        row.addWidget(new_song)
        return row

    def _lyrics_card(self) -> QtWidgets.QFrame:
        """A short hint and two actions above the lyrics table."""
        frame = widgets.card()
        column = QtWidgets.QVBoxLayout(frame)
        column.setContentsMargins(0, 8, 0, 0)
        column.addLayout(self._tools())
        self.table = lyrics_table.LyricsTable()
        column.addWidget(self.table, 1)
        return frame

    def _tools(self) -> QtWidgets.QHBoxLayout:
        """How to use the lyrics, then Copy all and Save."""
        tools = QtWidgets.QHBoxLayout()
        tools.setContentsMargins(16, 0, 16, 0)
        hint = i18n.tr(
            "Click a line to copy it. Double-click a word to fix it."
        )
        tools.addWidget(widgets.label(hint, "muted"), 1)
        for text, signal in (
            (i18n.tr("Copy all"), self.copy_all),
            (i18n.tr("Save…"), self.save),
        ):
            action = widgets.button(text)
            action.clicked.connect(signal)
            tools.addWidget(action)
        return tools

    def set_song(self, name: str) -> None:
        """Name the song whose words are shown."""
        self.song.setText(name)
