"""Automatic language selection and accurate, monotonic audio coverage."""

from unittest import mock

import pytest

from speech_translate import config
from speech_translate.speech import detection, progress


@pytest.mark.parametrize("language", config.LANGUAGES)
def test_automatic_language(language):
    """Carry detected language and confidence through all supported choices."""
    model = mock.Mock()
    model.detect_language.return_value = (language, 0.93, [])
    assert detection.detect(model, [0.1], None, config.Operation()) == (
        language,
        0.93,
    )
    assert model.detect_language.call_args.kwargs["vad_filter"] is True


def test_language_override_and_vad_fallback():
    """Use an explicit override, or retry unfiltered audio when VAD fails."""
    model = mock.Mock()
    assert detection.detect(model, [], "he", config.Operation()) == ("he", 1)
    model.detect_language.assert_not_called()
    model.detect_language.side_effect = [
        ValueError("No voices"),
        ("pl", 0.6, []),
    ]
    assert detection.detect(model, [0.1], None, config.Operation()) == (
        "pl",
        0.6,
    )
    assert "vad_filter" not in model.detect_language.call_args.kwargs


def test_unsupported_detection_explains_override():
    """Explain unsupported detection instead of silently choosing a language."""
    model = mock.Mock()
    model.detect_language.return_value = ("fr", 0.95, [])
    with pytest.raises(config.AppError, match="Language settings"):
        detection.detect(model, [0.1], None, config.Operation())


def test_coverage_never_reverses_or_claims_completion():
    """Clamp timestamp corrections and reserve 100% for completed cleanup."""
    updates = []
    tracker = progress.Coverage(
        120, config.Operation(lambda *x: updates.append(x))
    )
    for seconds in (0, 12, 8, 60, 140):
        tracker.update(seconds)
    assert [percent for _, percent in updates] == [0, 10, 10, 50, 99]
    assert "2:00 / 2:00" in updates[-1][0]
    assert progress.timestamp(-1) == "0:00"
    assert progress.timestamp(3661) == "61:01"
