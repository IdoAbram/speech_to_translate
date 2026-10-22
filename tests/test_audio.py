"""Actual audio decoding, digital silence, and quiet-sample preservation."""

import numpy as np
import pytest

from speech_translate import config
from speech_translate.speech import audio
from tests import helpers


def test_actual_silence(tmp_path):
    """Reject a truly silent WAV without hallucinating a transcript."""
    path = tmp_path / "silence.wav"
    helpers.write_silence(path)
    with pytest.raises(config.AppError, match="silent"):
        audio.load(path)


def test_actual_corrupt_audio(tmp_path):
    """Give a readable error for undecodable bytes."""
    path = tmp_path / "broken.mp3"
    path.write_bytes(b"not an MP3")
    with pytest.raises(config.AppError, match="Could not read"):
        audio.load(path)


def test_quiet_audio_is_not_discarded(tmp_path, monkeypatch):
    """Do not use an energy threshold that could erase quiet sung vocals."""
    from faster_whisper import audio as decoder

    samples = np.array([0.0, 0.000001, 0.0], dtype=np.float32)
    monkeypatch.setattr(
        decoder, "decode_audio", lambda *args, **kwargs: samples
    )
    assert audio.load(tmp_path / "quiet.mp3") is samples
