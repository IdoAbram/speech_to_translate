"""The working screen: one big bar, a percentage, and three plain steps.

Progress only moves forward and only on confirmed work; the elapsed timer
shows that something is happening between progress updates.
"""

import time

from PySide6 import QtCore, QtWidgets

from speech_translate import i18n
from speech_translate.gui import widgets
from speech_translate.speech.progress import timestamp


def steps() -> tuple[str, str, str]:
    """Name the three steps in the interface language."""
    return (
        i18n.tr("Reading the song"),
        i18n.tr("Hearing the words"),
        i18n.tr("Translating"),
    )


def titles() -> tuple[str, str, str]:
    """Describe the current step as a short sentence in progress."""
    return (
        i18n.tr("Reading the song…"),
        i18n.tr("Hearing the words…"),
        i18n.tr("Translating…"),
    )


class Activity(QtWidgets.QFrame):
    """A centered card that explains, in plain words, what is happening."""

    def __init__(self):
        """Build the card; the timer runs only while busy."""
        super().__init__()
        self.setObjectName("card")
        self.started = 0.0
        self.highwater = 0
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.tick)
        self._build()
        self.animation = QtCore.QPropertyAnimation(self.bar, b"value", self)
        self.animation.setDuration(350)
        self.set_stage(0)
        self.set_busy(False)

    def _build(self) -> None:
        """Stack the song, title, bar, steps, and Cancel from top down."""
        column = QtWidgets.QVBoxLayout(self)
        column.setContentsMargins(48, 36, 48, 36)
        column.setSpacing(18)
        self.song = widgets.label("", "muted")
        self.status = widgets.label("", "bigTitle")
        calm = i18n.tr("You can wait calmly; this takes about a minute.")
        for widget in (self.song, self.status, widgets.label(calm, "hint")):
            column.addWidget(widget, 0, QtCore.Qt.AlignmentFlag.AlignCenter)
        column.addWidget(self._progress())
        column.addLayout(self._steps())
        self.detail = widgets.label("", "caption")
        self.detail.setWordWrap(True)
        column.addWidget(self.detail)
        self.cancel = widgets.button(i18n.tr("Cancel"))
        column.addWidget(self.cancel, 0, QtCore.Qt.AlignmentFlag.AlignCenter)

    def _progress(self) -> QtWidgets.QWidget:
        """A thick bar with the percentage and elapsed time below it."""
        box = QtWidgets.QWidget()
        column = QtWidgets.QVBoxLayout(box)
        column.setContentsMargins(0, 0, 0, 0)
        self.bar = QtWidgets.QProgressBar()
        self.bar.setTextVisible(False)
        row = QtWidgets.QHBoxLayout()
        self.percent = widgets.label("", "settingsHeading")
        self.elapsed = widgets.label("", "muted")
        self.elapsed.setObjectName("elapsed")
        row.addWidget(self.percent)
        row.addStretch()
        row.addWidget(self.elapsed)
        column.addWidget(self.bar)
        column.addLayout(row)
        return box

    def _steps(self) -> QtWidgets.QVBoxLayout:
        """Three numbered steps that are ticked off as work completes."""
        column = QtWidgets.QVBoxLayout()
        column.setSpacing(8)
        self.step_labels = [widgets.label() for _ in steps()]
        for step in self.step_labels:
            column.addWidget(step)
        return column

    def set_song(self, name: str) -> None:
        """Name the song being worked on."""
        self.song.setText(name)

    def set_stage(self, stage: int) -> None:
        """Mark earlier steps done, the current one bold, later ones grey."""
        self.status.setText(titles()[stage])
        for index, (step, text) in enumerate(zip(self.step_labels, steps())):
            done, now = index < stage, index == stage
            mark = "✓" if done else str(index + 1)
            step.setText(f"{mark}   {text}")
            name = "stepDone" if done else "stepNow" if now else "stepLater"
            step.setObjectName(name)
            step.style().unpolish(step)
            step.style().polish(step)

    def set_busy(self, busy: bool) -> None:
        """Start a fresh operation timer and stop it on every outcome."""
        self.bar.setVisible(busy)
        self.cancel.setEnabled(busy)
        if busy:
            self.started = time.monotonic()
            self.highwater = 0
            self.bar.setRange(0, 0)
            self.timer.start()
            self.tick()
        else:
            self.timer.stop()
            self.animation.stop()

    def tick(self) -> None:
        """Confirm that work is ongoing even during a long decoder pass."""
        elapsed = timestamp(time.monotonic() - self.started)
        self.elapsed.setText(i18n.tr("{elapsed} so far", elapsed=elapsed))
        measured = bool(self.bar.maximum())
        self.percent.setText(f"{self.highwater}%" if measured else "")

    def report(self, message: str, percent: int) -> None:
        """Animate only toward confirmed progress and never move backward."""
        self.detail.setText(message)
        if percent < 0:
            return
        self.highwater = max(self.highwater, min(100, percent))
        previous = max(0, self.bar.value()) if self.bar.maximum() else 0
        self.bar.setRange(0, 100)
        self.animation.stop()
        self.animation.setStartValue(previous)
        self.animation.setEndValue(self.highwater)
        self.animation.start()
        self.tick()
