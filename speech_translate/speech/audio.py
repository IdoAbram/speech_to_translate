"""Decode local audio once and reject truly silent recordings."""

import pathlib

import numpy as np

from speech_translate import config, i18n


def load(path: pathlib.Path) -> np.ndarray:
    """Return 16 kHz mono samples without trimming music or quiet vocals."""
    from faster_whisper import audio

    try:
        samples = audio.decode_audio(str(path), sampling_rate=16000)
    except (ValueError, OSError) as error:
        raise config.AppError(
            i18n.tr("Could not read the audio: {error}", error=error)
        ) from error
    if not samples.size or not np.any(samples):
        raise config.AppError(
            i18n.tr("No vocals were found. This recording is silent.")
        )
    return samples
