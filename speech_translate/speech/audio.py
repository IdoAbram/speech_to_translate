"""Decode local audio once and reject truly silent recordings."""

import pathlib

import numpy as np

from speech_translate import config


def load(path: pathlib.Path) -> np.ndarray:
    """Return 16 kHz mono samples without trimming music or quiet vocals."""
    from faster_whisper import audio

    try:
        samples = audio.decode_audio(str(path), sampling_rate=16000)
    except (ValueError, OSError) as error:
        raise config.AppError(f"Could not read the audio: {error}") from error
    if not samples.size or not np.any(samples):
        raise config.AppError("No vocals were found. This recording is silent.")
    return samples
