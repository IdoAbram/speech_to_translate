"""Measured progress and elapsed time without speculative completion dates."""

import time

from PySide6 import QtCore, QtWidgets

from speech_translate.speech.progress import timestamp


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
        self.status = QtWidgets.QLabel(
            "Drop an MP3 to get started. Language is detected automatically."
        )
        self.status.setTextFormat(QtCore.Qt.TextFormat.PlainText)
        self.status.setWordWrap(True)
        self.elapsed = QtWidgets.QLabel()
        self.elapsed.setObjectName("elapsed")
        self.cancel = QtWidgets.QPushButton("Cancel")
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
        coverage = f" · {self.highwater}%" if self.bar.maximum() else ""
        self.elapsed.setText(f"Working{coverage} · {elapsed} elapsed")

    def report(self, message: str, percent: int) -> None:
        """Animate only toward confirmed progress and never move backward."""
        self.status.setText(message)
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
