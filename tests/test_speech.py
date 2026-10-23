"""Speech service validation, inference configuration, and resource cleanup."""

import contextlib
import threading
import types
from unittest import mock

import pytest

from speech_translate import config
from speech_translate.speech import audio, engine, service
from tests import helpers


@pytest.fixture(autouse=True)
def decoded_audio(monkeypatch):
    """Isolate model orchestration from the independently tested decoder."""
    monkeypatch.setattr(audio, "load", lambda path: [0.1, 0.2])


@pytest.mark.parametrize("size", ["invalid", "small"])
def test_missing_or_invalid_model(tmp_path, size):
    """Fail locally when speech weights are missing or misnamed."""
    with pytest.raises(config.AppError):
        engine.model_path(tmp_path, size)


def test_audio_validation(tmp_path):
    """Reject both missing and zero-byte inputs before inference."""
    path = tmp_path / "empty.mp3"
    with pytest.raises(config.AppError, match="existing"):
        service.validate_audio(path)
    path.touch()
    with pytest.raises(config.AppError, match="empty"):
        service.validate_audio(path)


def test_song_options_and_timestamps(song):
    """Disable VAD for songs and request word-level timing."""
    model = mock.Mock()
    word = types.SimpleNamespace(start=0, end=1, word="Hello")
    segment = helpers.raw_segment(words=[word])
    model.transcribe.return_value = (
        iter_as_generator([segment]),
        types.SimpleNamespace(duration=2),
    )
    result = engine.recognize(model, song, "he", config.Operation())
    assert result.segments[0].words[0].text == "Hello"
    assert model.transcribe.call_args.kwargs["vad_filter"] is False
    assert model.transcribe.call_args.kwargs["word_timestamps"] is True
    assert model.transcribe.call_args.kwargs["language"] == "he"


def iter_as_generator(values):
    """Provide the closable lazy iterator returned by faster-whisper."""
    yield from values


def test_empty_result_and_decoder_error(song):
    """Turn absent vocals and corrupt audio into actionable errors."""
    model = mock.Mock()
    model.transcribe.return_value = (
        iter_as_generator([]),
        types.SimpleNamespace(duration=2),
    )
    with pytest.raises(config.AppError, match="No vocals"):
        engine.recognize(model, song, "en", config.Operation())
    model.transcribe.side_effect = ValueError("broken")
    with pytest.raises(config.AppError, match="Could not read"):
        engine.recognize(model, song, "en", config.Operation())


def test_speech_service_orchestration(song, monkeypatch):
    """Return line-formatted text and report completion through the API."""
    model = mock.Mock()
    model.transcribe.return_value = (
        iter_as_generator([helpers.raw_segment()]),
        types.SimpleNamespace(duration=2),
    )
    monkeypatch.setattr(engine, "model_path", lambda *args: song.parent)
    monkeypatch.setattr(
        engine, "open_model", lambda path: contextlib.nullcontext(model)
    )
    updates = []
    result = service.transcribe(
        song, "en", progress=lambda *args: updates.append(args)
    )
    assert result.text == "Hello"
    assert updates[-1][1] == 100


def test_cancel_before_loading(song):
    """Do no model work after cancellation was already requested."""
    event = threading.Event()
    event.set()
    with pytest.raises(config.Cancelled):
        service.transcribe(song, "en", cancel=event)


def test_model_cleanup_on_failure(tmp_path, monkeypatch):
    """Unload native weights even when recognition raises an exception."""
    import faster_whisper

    model = mock.Mock()
    factory = mock.Mock(return_value=model)
    monkeypatch.setattr(faster_whisper, "WhisperModel", factory)
    with pytest.raises(ValueError), engine.open_model(tmp_path):
        raise ValueError("failed recognition")
    model.model.unload_model.assert_called_once()
    assert factory.call_args.kwargs["local_files_only"] is True
    assert factory.call_args.kwargs["compute_type"] == "int8"
