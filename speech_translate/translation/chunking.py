"""Bound model inputs without dropping text or splitting lyric lines away."""

import re

from speech_translate import config, i18n

TOKEN_LIMIT = 256


def split_for_model(text: str, tokenizer, limit: int = TOKEN_LIMIT) -> list:
    """Keep connected sentences together until the token budget is reached."""
    if limit < 1:
        raise ValueError("Token limit must be positive.")
    return (
        bounded_chunks(text.strip(), tokenizer, limit) if text.strip() else []
    )


def bounded_chunks(text: str, tokenizer, limit: int) -> list:
    """Split oversized phrases at nearby spaces, then characters if needed."""
    tokens = tokenizer.encode(text, out_type=str)
    if len(tokens) <= limit:
        return [tokens] if tokens else []
    cut = split_position(text)
    if not cut:
        raise config.AppError(
            i18n.tr("A text fragment exceeds the model limit.")
        )
    left = bounded_chunks(text[:cut].strip(), tokenizer, limit)
    return left + bounded_chunks(text[cut:].strip(), tokenizer, limit)


def split_position(text: str) -> int:
    """Find a space near the midpoint or fall back to a character boundary."""
    middle = len(text) // 2
    sentences = [
        match.end()
        for match in re.finditer(r"[.!?。！？]\s+", text)
        if 0 < match.end() < len(text)
    ]
    if sentences:
        return min(sentences, key=lambda index: abs(index - middle))
    spaces = [
        match.start()
        for match in re.finditer(r"\s+", text)
        if 0 < match.start() < len(text) - 1
    ]
    return (
        min(spaces, key=lambda index: abs(index - middle)) if spaces else middle
    )
