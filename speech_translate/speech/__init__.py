"""Speech recognition and timestamp-based song formatting."""

from speech_translate.speech.records import Segment, Transcript, Word
from speech_translate.speech.service import transcribe

__all__ = ["Segment", "Transcript", "Word", "transcribe"]
