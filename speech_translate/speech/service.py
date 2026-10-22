"""Public speech-to-text operation."""

import pathlib

from speech_translate import config
from speech_translate.speech import engine, records


def validate_audio(audio_path: str | pathlib.Path) -> pathlib.Path:
    """Require an existing, nonempty audio file before loading any model."""
    path = pathlib.Path(audio_path)
    if not path.is_file():
        raise config.AppError("Choose an existing MP3 file.")
    if not path.stat().st_size:
        raise config.AppError("This audio file is empty.")
    return path


def transcribe(
    audio_path,
    language: str | None = None,
    model_size: str = "small",
    *,
    models_dir=config.MODELS,
    progress=config.ignore_progress,
    cancel=None,
) -> records.Transcript:
    """Transcribe a local recording and return timed, song-formatted text."""
    operation = config.Operation(progress, cancel)
    operation.check()
    path, weights = prepare_input(audio_path, language, model_size, models_dir)
    operation.report("Loading the speech model…")
    with engine.open_model(weights) as model:
        result = engine.recognize(model, path, language, operation)
    operation.report("Transcript ready.", 100)
    return result


def prepare_input(audio_path, language: str, size: str, models_dir) -> tuple:
    """Validate language and local assets before importing inference code."""
    if language is not None:
        config.validate_language(language)
    path = validate_audio(audio_path)
    weights = engine.model_path(models_dir, size)
    config.offline_mode()
    return path, weights
