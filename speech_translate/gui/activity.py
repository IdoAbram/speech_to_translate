"""Measured progress and elapsed time without speculative completion dates."""

import time

from PySide6 import QtCore, QtWidgets

from speech_translate import i18n
from speech_translate.speech.progress import timestamp

KINDS = ("info", "success", "warning", "error")


class Activity(QtWidgets.QWidget):
    """Show an active timer while a model is working between progress events."""

    def __init__(self):
        """Build a compact progress area with a cancellation action."""
        super().__init__()
        self.started = 0.0
        self.highwater = 0
        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(500)
        self.timer.timeout.connect(self.tick)
        self._build()
        self.animation = QtCore.QPropertyAnimation(self.bar, b"value", self)
        self.animation.setDuration(350)
        self.set_busy(False)

    def _build(self) -> None:
        """Keep status messages readable even after an operation finishes."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.status = QtWidgets.QLabel(i18n.tr("Choose a song to begin."))
        self.status.setObjectName("status")
        self.status.setTextFormat(QtCore.Qt.TextFormat.PlainText)
        self.status.setWordWrap(True)
        self.elapsed = QtWidgets.QLabel()
        self.elapsed.setObjectName("elapsed")
        self.cancel = QtWidgets.QPushButton(i18n.tr("Cancel"))
        self.bar = QtWidgets.QProgressBar()
        self.bar.setTextVisible(False)
        row = QtWidgets.QHBoxLayout()
        row.addWidget(self.status, 1)
        row.addWidget(self.elapsed)
        row.addWidget(self.cancel)
        layout.addLayout(row)
        layout.addWidget(self.bar)

    def set_busy(self, busy: bool) -> None:
        """Start a fresh operation timer and stop it on every outcome."""
        self.bar.setVisible(busy)
        self.cancel.setVisible(busy)
        self.cancel.setEnabled(busy)
        self.elapsed.setVisible(busy)
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
        if self.bar.maximum():
            text = i18n.tr(
                "Working · {percent}% · {elapsed}",
                percent=self.highwater,
                elapsed=elapsed,
            )
        else:
            text = i18n.tr("Working · {elapsed}", elapsed=elapsed)
        self.elapsed.setText(text)

    def report(self, message: str, percent: int) -> None:
        """Animate only toward confirmed progress and never move backward."""
        self.show(message, "info")
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

    def show(self, message: str, kind: str = "info") -> None:
        """Show a message colored by its kind: info, success, warning, error."""
        if kind not in KINDS:
            raise ValueError(f"Unknown status kind: {kind}")
        self.status.setText(message)
        self.status.setProperty("kind", kind)
        self.status.style().unpolish(self.status)
        self.status.style().polish(self.status)
