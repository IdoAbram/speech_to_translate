"""Immutable speech results, independent of the inference library."""

import dataclasses

from speech_translate.speech import formatting


@dataclasses.dataclass(frozen=True)
class Word:
    """A recognized word and its start/end times in seconds."""

    start: float
    end: float
    text: str


@dataclasses.dataclass(frozen=True)
class Segment:
    """A recognized phrase with optional individual word timestamps."""

    start: float
    end: float
    text: str
    words: tuple[Word, ...] = ()


@dataclasses.dataclass(frozen=True)
class Transcript:
    """Source language, recognized phrases, and recording duration."""

    language: str
    segments: tuple[Segment, ...]
    duration: float
    confidence: float = 1.0

    @property
    def text(self) -> str:
        """Return inferred song lines, keeping repeats and longer pauses."""
        return formatting.format_lyrics(self.segments)
