"""Real local-model checks, enabled explicitly with RUN_MODEL_TESTS=1."""

import os
import threading

import pytest

from speech_translate import config, speech, translation
from tests import helpers

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_MODEL_TESTS") != "1", reason="Local model opt-in"
    ),
]
EXAMPLES = {
    "en": "Good morning\nSing again\n\nSing again",
    "he": "בוקר טוב\nלשיר שוב\n\nלשיר שוב",
    "pl": "Dzień dobry\nZaśpiewaj ponownie\n\nZaśpiewaj ponownie",
}
PAIRS = [(a, b) for a in EXAMPLES for b in EXAMPLES if a != b]


@pytest.mark.parametrize(("source", "target"), PAIRS)
def test_real_translation_preserves_song_layout(source, target):
    """Translate all six routes with real weights and blocked sockets."""
    output = translation.translate(EXAMPLES[source], source, target)
    stanzas = output.split("\n\n")
    assert len(stanzas) == 2
    assert all(part.strip() for part in stanzas)
    assert "▁" not in output
    assert output != EXAMPLES[source]


@pytest.fixture
def real_mp3(tmp_path):
    """Encode the checked-in synthetic speech as an actual MP3."""
    source = config.ROOT / "tests" / "fixtures" / "sample.wav"
    destination = tmp_path / "sample.mp3"
    helpers.encode_mp3(source, destination)
    return destination


def test_real_mp3_transcript(real_mp3):
    """Verify actual audio decoding and timestamped recognition."""
    result = speech.transcribe(real_mp3)
    assert result.language == "en"
    words = result.text.lower().split()
    assert "meeting" in words and "tomorrow" in words
    assert result.segments and result.duration > 1
    assert any(segment.words for segment in result.segments)


def test_real_silence_and_corrupt_audio(tmp_path):
    """Check no-vocal and decoding failures with the installed speech model."""
    path = tmp_path / "silence.wav"
    helpers.write_silence(path)
    with pytest.raises(config.AppError, match="No vocals"):
        speech.transcribe(path, "en")
    path.write_bytes(b"not audio")
    with pytest.raises(config.AppError, match="Could not read"):
        speech.transcribe(path, "pl")


def test_real_translation_cancel():
    """Stop after a completed line without producing partial final output."""
    cancel = threading.Event()

    def on_progress(message, percent):
        if percent > 0:
            cancel.set()

    with pytest.raises(config.Cancelled):
        translation.translate(
            EXAMPLES["en"], "en", "he", progress=on_progress, cancel=cancel
        )


def test_real_desktop_pipeline(desktop, real_mp3, qapp):
    """Hear an English song and translate it with one click, as in the app."""
    desktop.accept_file(str(real_mp3))
    desktop.view.chosen.languages.set_languages("en", "he")
    desktop.view.chosen.translate.click()
    helpers.wait_runner(desktop.runner, qapp, timeout=240)
    table = desktop.view.result.table
    words = "\n".join(table.source_lines())
    assert "meeting" in words.lower(), desktop.view.status.text()
    assert any(table.translated_lines()), desktop.view.status.text()
    assert desktop.view.page() == "result"
