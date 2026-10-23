"""Suggest lyric spacing from timing, without inventing verse structure."""

from __future__ import annotations

import re
import textwrap
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from speech_translate.speech import records

LINE_WIDTH = 60
LINE_PAUSE = 0.8
STANZA_PAUSE = 2.5


def clean_text(text: str) -> str:
    """Normalize whitespace and remove spaces before common punctuation."""
    return re.sub(r"\s+([,.;:!?])", r"\1", " ".join(text.split()))


def word_lines(words: tuple[records.Word, ...]) -> list[tuple]:
    """Group timed words into short lines without removing repetitions."""
    lines = []
    group = []
    for word in words:
        if group and needs_break(group, word):
            lines.append(pack_line(group))
            group = []
        group.append(word)
    if group:
        lines.append(pack_line(group))
    return lines


def needs_break(group: list, word: records.Word) -> bool:
    """Return whether a word starts a new phrase or exceeds the line width."""
    text = clean_text(" ".join(item.text for item in [*group, word]))
    return word.start - group[-1].end >= LINE_PAUSE or len(text) > LINE_WIDTH


def pack_line(words: list) -> tuple[float, float, str]:
    """Convert a group of words into one timed line."""
    text = clean_text(" ".join(word.text for word in words))
    return words[0].start, words[-1].end, text


def segment_lines(segment: records.Segment) -> list[tuple]:
    """Use word timing when available, otherwise wrap the original phrase."""
    if segment.words:
        return word_lines(segment.words)
    lines = textwrap.wrap(
        clean_text(segment.text),
        width=LINE_WIDTH,
        break_long_words=False,
        break_on_hyphens=False,
    )
    return [(segment.start, segment.end, line) for line in lines]


def format_lyrics(segments: tuple[records.Segment, ...]) -> str:
    """Keep phrase breaks and insert blank lines after long vocal pauses."""
    output = []
    previous_end = None
    for segment in segments:
        for start, end, text in segment_lines(segment):
            if not text:
                continue
            if (
                previous_end is not None
                and start - previous_end >= STANZA_PAUSE
            ):
                output.append("")
            output.append(text)
            previous_end = end
    return "\n".join(output)
