"""Background operations with no direct dependency on window widgets."""

import dataclasses
import logging
import threading

from PySide6 import QtCore

from speech_translate import config, speech, translation


@dataclasses.dataclass(frozen=True)
class Request:
    """One transcription or translation requested by the GUI."""

    action: str
    source: str | None = None
    target: str = "en"
    path: str = ""
    text: str = ""


class Worker(QtCore.QObject):
    """Perform inference off the UI thread and communicate through signals."""

    progress = QtCore.Signal(str, int)
    result = QtCore.Signal(object)
    failed = QtCore.Signal(str)
    finished = QtCore.Signal()

    def __init__(self, request: Request):
        """Store immutable input and a thread-safe cancellation event."""
        super().__init__()
        self.request = request
        self.cancel = threading.Event()

    @QtCore.Slot()
    def run(self) -> None:
        """Report every outcome and always release the worker thread."""
        try:
            self.result.emit(self._execute())
        except (config.AppError, OSError, ValueError) as error:
            self.failed.emit(str(error))
        except Exception as error:  # A worker must never strand the UI.
            logging.exception("Background inference failed")
            self.failed.emit(f"Processing failed: {error}")
        finally:
            self.finished.emit()

    def _execute(self) -> speech.Transcript | str:
        """Dispatch one of the two stages using the captured input."""
        request = self.request
        options = {"progress": self.progress.emit, "cancel": self.cancel}
        if request.action == "speech":
            return speech.transcribe(request.path, request.source, **options)
        if request.action == "translate":
            return translation.translate(
                request.text,
                request.source,
                request.target,
                **options,
            )
        raise ValueError(f"Unknown operation: {request.action}")
