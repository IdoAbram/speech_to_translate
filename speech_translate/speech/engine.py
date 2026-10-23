"""Local faster-whisper loading and conversion to application records."""

import contextlib
import gc
import pathlib

from speech_translate import config, i18n
from speech_translate.speech import audio, detection, progress, records

MODEL_FILES = ("model.bin", "config.json", "tokenizer.json")
SONG_OPTIONS = {
    "task": "transcribe",
    "beam_size": 5,
    "vad_filter": False,
    "word_timestamps": True,
    "condition_on_previous_text": False,
    "hallucination_silence_threshold": 2.0,
}


def model_path(models_dir: pathlib.Path, size: str) -> pathlib.Path:
    """Return an installed speech model or explain how to install it."""
    if size not in config.SPEECH_MODELS:
        raise config.AppError(
            i18n.tr("Choose a base, small, or medium speech model.")
        )
    path = pathlib.Path(models_dir) / "speech" / size
    if not all((path / name).is_file() for name in MODEL_FILES):
        raise config.AppError(
            i18n.tr(
                "Missing {size} model. Run python setup_models.py "
                "--speech-model {size} on a connected computer first.",
                size=size,
            )
        )
    return path


@contextlib.contextmanager
def open_model(path: pathlib.Path):
    """Load only local CPU weights and release them after transcription."""
    from faster_whisper import WhisperModel  # Load heavy dependencies lazily.

    model = WhisperModel(
        str(path),
        device="cpu",
        compute_type="int8",
        cpu_threads=config.THREADS,
        num_workers=1,
        local_files_only=True,
    )
    try:
        yield model
    finally:
        model.model.unload_model()
        del model
        gc.collect()


def recognize(model, path: pathlib.Path, language: str, operation):
    """Read song audio without speech-only VAD trimming sung vocals."""
    operation.report(i18n.tr("Reading the audio file…"))
    samples = audio.load(path)
    language, confidence = detection.detect(model, samples, language, operation)
    result, duration = decode(model, samples, language, operation)
    if not result:
        raise config.AppError(
            i18n.tr("No vocals were found. Try a clearer recording.")
        )
    return records.Transcript(language, tuple(result), duration, confidence)


def decode(model, samples, language: str, operation) -> tuple:
    """Consume the lazy decoder while keeping its native generator scoped."""
    operation.report(
        i18n.tr("Transcribing audio · Waiting for the first passage…"), 0
    )
    try:
        segments, info = model.transcribe(
            samples,
            language=language,
            **SONG_OPTIONS,
        )
        with contextlib.closing(segments):
            return collect_segments(
                segments, info.duration, operation
            ), info.duration
    except (ValueError, OSError) as error:
        raise config.AppError(
            i18n.tr("Could not read the audio: {error}", error=error)
        ) from error


def collect_segments(segments, duration: float, operation) -> list:
    """Consume lazy recognition results with cancellation and progress."""
    result = []
    coverage = progress.Coverage(duration, operation)
    coverage.update(0)
    for segment in segments:
        coverage.update(segment.end)
        if segment.text.strip():
            result.append(convert_segment(segment))
    operation.check()
    return result


def convert_segment(segment) -> records.Segment:
    """Copy library records so the app does not retain the loaded model."""
    words = tuple(
        records.Word(word.start, word.end, word.word)
        for word in (segment.words or [])
        if word.word.strip()
    )
    return records.Segment(
        segment.start,
        segment.end,
        segment.text.strip(),
        words,
    )
