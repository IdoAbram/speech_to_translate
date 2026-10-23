"""The 'song chosen' screen and the 'translated' screen."""

from PySide6 import QtCore, QtWidgets

from speech_translate import config, i18n
from speech_translate.gui import language_bar, lyrics_box, widgets


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
    """Screen 4: compact controls on top, two lyrics boxes below."""

    new_song = QtCore.Signal()
    translate_requested = QtCore.Signal()
    copy_all = QtCore.Signal()
    copy_source = QtCore.Signal()
    save = QtCore.Signal()
    edited = QtCore.Signal()
    line_clicked = QtCore.Signal(int)

    def __init__(self):
        """Give the lyrics most of the window."""
        super().__init__()
        column = QtWidgets.QVBoxLayout(self)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(14)
        column.addWidget(self._top_card())
        column.addLayout(self._lyrics_boxes(), 1)
        self._connect_boxes()

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

    def _lyrics_boxes(self) -> QtWidgets.QHBoxLayout:
        """The song's words and the translation, in two boxes side by side."""
        row = QtWidgets.QHBoxLayout()
        row.setSpacing(16)
        self.source = lyrics_box.LyricsBox(
            i18n.tr("You can fix a misheard word here."),
            False,
            [self._action(i18n.tr("Copy"), self.copy_source)],
        )
        self.translation = lyrics_box.LyricsBox(
            i18n.tr("Click a line to copy it."),
            True,
            [
                self._action(i18n.tr("Copy"), self.copy_all),
                self._action(i18n.tr("Save…"), self.save),
            ],
        )
        row.addWidget(self.source)
        row.addWidget(self.translation)
        return row

    @staticmethod
    def _action(text: str, signal) -> QtWidgets.QPushButton:
        """A small button that emits one of the page's signals."""
        action = widgets.button(text)
        action.clicked.connect(signal)
        return action

    def _connect_boxes(self) -> None:
        """Report edits and clicks, and scroll both boxes together."""
        source, target = self.source.editor, self.translation.editor
        source.textChanged.connect(self.edited)
        target.line_clicked.connect(self.line_clicked)
        for one, other in ((source, target), (target, source)):
            one.verticalScrollBar().valueChanged.connect(
                other.verticalScrollBar().setValue
            )

    def set_headers(self, source: str, target: str) -> None:
        """Name both languages and lay each box out in its direction."""
        self.source.title.setText(
            i18n.tr(
                "Song words · {language}", language=config.language_name(source)
            )
        )
        self.translation.title.setText(
            i18n.tr(
                "Translation · {language}",
                language=config.language_name(target),
            )
        )
        self.source.editor.set_language(source)
        self.translation.editor.set_language(target)

    def set_lines(self, source_lines: list, translated=None) -> None:
        """Show the words and, when known, their line-by-line translation."""
        self.source.editor.set_lines(source_lines)
        self.translation.editor.set_lines(translated or [])

    def source_lines(self) -> list:
        """Return the song's lines, including any fixes."""
        return self.source.editor.lines()

    def translated_lines(self) -> list:
        """Return the translation's lines, or nothing before translating."""
        lines = self.translation.editor.lines()
        return lines if any(lines) else []

    def clear_translation(self) -> None:
        """Remove a translation that no longer matches the words."""
        self.translation.editor.set_lines([])

    def set_song(self, name: str) -> None:
        """Name the song whose words are shown."""
        self.song.setText(name)
