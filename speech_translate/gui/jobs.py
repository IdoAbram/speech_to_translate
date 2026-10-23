"""Ownership and cleanup of the single desktop inference thread."""

from PySide6 import QtCore

from speech_translate.gui import worker


class JobRunner(QtCore.QObject):
    """Run one request at a time without blocking the Qt event loop."""

    progress = QtCore.Signal(str, int)
    result = QtCore.Signal(object)
    failed = QtCore.Signal(str)
    busy_changed = QtCore.Signal(bool)

    def __init__(self, parent=None):
        """Initialize an idle runner owned by the window."""
        super().__init__(parent)
        self._thread = None
        self._worker = None

    @property
    def busy(self) -> bool:
        """Return whether a worker still owns the model operation."""
        return self._thread is not None

    def start(self, request: worker.Request) -> None:
        """Start a captured request, rejecting overlapping operations."""
        if self.busy:
            raise RuntimeError("Another operation is already running.")
        self._thread = QtCore.QThread(self)
        self._worker = worker.Worker(request)
        self._worker.moveToThread(self._thread)
        self._connect_worker()
        self.busy_changed.emit(True)
        self._thread.start()

    def _connect_worker(self) -> None:
        """Connect results and keep thread teardown in the GUI thread."""
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self.progress)
        self._worker.result.connect(self.result)
        self._worker.failed.connect(self.failed)
        self._worker.finished.connect(self._thread.quit)
        self._worker.finished.connect(self._worker.deleteLater)
        self._thread.finished.connect(self._finish)
        self._thread.finished.connect(self._thread.deleteLater)

    @QtCore.Slot()
    def _finish(self) -> None:
        """Wait for native cleanup before exposing the runner as idle."""
        self._thread.wait()
        self._thread = None
        self._worker = None
        self.busy_changed.emit(False)

    def cancel(self) -> None:
        """Request cancellation without touching any worker-owned model."""
        if self._worker is not None:
            self._worker.cancel.set()
