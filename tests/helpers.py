"""Small test fixtures shared across model and interface tests."""

import time
import types
import wave

from PySide6 import QtCore


class CharacterTokenizer:
    """Expose token limits deterministically, including Unicode input."""

    def encode(self, text, out_type=str):
        """Treat every character as a token."""
        return list(text)

    def decode(self, tokens):
        """Restore exactly the supplied characters."""
        return "".join(tokens)

    def prepare(self, tokens):
        """Leave deterministic fixture tokens unchanged for inference."""
        return tokens


def make_multilingual(root):
    """Create the complete multilingual runtime asset inventory."""
    path = root / "translation" / "nllb"
    (path / "model").mkdir(parents=True, exist_ok=True)
    for name in (
        "model/model.bin",
        "model/config.json",
        "model/shared_vocabulary.json",
        "sentencepiece.bpe.model",
    ):
        (path / name).write_bytes(b"fixture")
    return path


def raw_segment(text="Hello", start=0.0, end=1.0, words=None):
    """Represent a lazy faster-whisper result without loading its model."""
    return types.SimpleNamespace(text=text, start=start, end=end, words=words)


def wait_runner(runner, app, timeout=5):
    """Process Qt events while releasing the GIL for Python worker code."""
    deadline = time.monotonic() + timeout
    while runner.busy and time.monotonic() < deadline:
        app.processEvents()
        time.sleep(0.01)
    assert not runner.busy, "Background operation did not finish"
    QtCore.QCoreApplication.sendPostedEvents(
        None, QtCore.QEvent.Type.DeferredDelete
    )


def write_silence(path):
    """Write three seconds of valid mono PCM for a real decoder check."""
    with wave.open(str(path), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(16000)
        output.writeframes(b"\0\0" * 16000 * 3)


def encode_mp3(source_path, destination):
    """Encode an existing local WAV fixture using the actual audio library."""
    import av

    with (
        av.open(str(source_path)) as source,
        av.open(str(destination), "w") as output,
    ):
        stream = output.add_stream("libmp3lame", rate=16000)
        stream.layout = "mono"
        for frame in source.decode(audio=0):
            for packet in stream.encode(frame):
                output.mux(packet)
        for packet in stream.encode():
            output.mux(packet)
