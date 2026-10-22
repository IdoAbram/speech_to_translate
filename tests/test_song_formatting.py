"""Song phrasing, repeated choruses, whitespace, and record formatting."""

import pytest

from speech_translate.speech import formatting, records


def test_phrase_and_stanza_spacing():
    """Keep repeated phrases and separate long pauses into stanzas."""
    segments = (
        records.Segment(0, 1, "  Sing   again !"),
        records.Segment(1.2, 2, "Sing again!"),
        records.Segment(5, 6, "A new verse."),
    )
    transcript = records.Transcript("en", segments, 6)
    assert transcript.text == "Sing again!\nSing again!\n\nA new verse."


def test_word_timing_breaks_inside_segments():
    """Recognize a phrase break and a stanza break within one segment."""
    words = (
        records.Word(0, 0.3, "Hello"),
        records.Word(0.4, 0.6, "world"),
        records.Word(1.5, 2, "Again"),
        records.Word(5, 6, "Tonight"),
    )
    segment = records.Segment(0, 6, "Hello world Again Tonight", words)
    assert (
        formatting.format_lyrics((segment,)) == "Hello world\nAgain\n\nTonight"
    )


@pytest.mark.parametrize(
    "phrase", ["שלום עולם", "Zażółć gęślą jaźń", "sing again"]
)
def test_wrapping_preserves_all_words(phrase):
    """Wrap long lines without splitting words or losing Unicode text."""
    text = " ".join([phrase] * 20)
    result = formatting.format_lyrics((records.Segment(0, 8, text),))
    assert result.split() == text.split()
    assert all(
        len(line) <= formatting.LINE_WIDTH for line in result.splitlines()
    )


def test_empty_and_untimed_segments():
    """Ignore blank phrases and leave long unbreakable words intact."""
    assert formatting.format_lyrics((records.Segment(0, 1, " "),)) == ""
    text = "x" * 100
    assert formatting.format_lyrics((records.Segment(0, 1, text),)) == text


def test_word_width_breaks_without_pauses():
    """Bound word-timed lines even during uninterrupted singing."""
    words = tuple(
        records.Word(i / 10, (i + 1) / 10, "again") for i in range(30)
    )
    lines = formatting.word_lines(words)
    assert len(lines) > 1
    assert " ".join(line[2] for line in lines).split() == ["again"] * 30
