"""Automatic language detection, with an optional user override."""

from speech_translate import config


def detect(model, samples, language, operation) -> tuple[str, float]:
    """Prefer vocal regions for detection without trimming the transcript."""
    if language:
        return language, 1.0
    operation.report("Identifying the song language…")
    code, confidence, _ = sample_language(model, samples)
    if code not in config.LANGUAGES:
        raise config.AppError(
            f"Detected language '{code}'. Open Language settings to choose "
            "English, Hebrew, or Polish if this detection is incorrect."
        )
    operation.report(f"Detected {config.LANGUAGES[code]}. Transcribing…", 0)
    return code, confidence


def sample_language(model, samples) -> tuple:
    """Prefer vocals for detection; fall back if VAD finds no speech."""
    options = {
        "language_detection_segments": 5,
        "language_detection_threshold": 0.8,
    }
    try:
        return model.detect_language(audio=samples, vad_filter=True, **options)
    except ValueError:
        return model.detect_language(audio=samples, **options)
