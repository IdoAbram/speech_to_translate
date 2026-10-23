"""Keep source lines aligned and recover from decoder output limits."""

import dataclasses
import re

from speech_translate import config
from speech_translate.translation import chunking, engine


def prepare(text: str, tokenizer) -> list:
    """Tokenize each source line separately so subtitles stay aligned.

    Args:
        text: Source text whose lines and blank lines must be preserved.
        tokenizer: Encodes content tokens for the translation model.

    Returns:
        One list of bounded token chunks per source line. Blank lines map
        to an empty list so the output keeps the same line structure.
    """
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    return [
        chunking.split_for_model(" ".join(line.split()), tokenizer)
        for line in lines
    ]


def translate_chunk(model, tokenizer, tokens, prefix, operation) -> str:
    """Retry exhausted decoding on smaller passages without truncation."""
    return PassageTranslator(model, tokenizer, prefix, operation).translate(
        tokens
    )


def identifiers(text: str) -> set[str]:
    """Find long numeric identifiers, tolerating thousands separators."""
    normalized = re.sub(r"(?<=\d)[, ](?=\d{3}\b)", "", text)
    return set(re.findall(r"\d{3,}", normalized))


@dataclasses.dataclass
class PassageTranslator:
    """Decode contextual passages with shared caching and bounded retries."""

    model: object
    tokenizer: object
    prefix: str
    operation: object
    cache: dict = dataclasses.field(default_factory=dict)

    def translate(self, tokens) -> str:
        """Retain repeated text while reusing successful retry fragments."""
        self.operation.check()
        key = tuple(tokens)
        if key not in self.cache:
            self.cache[key] = self.decode(tokens)
        return self.cache[key]

    def decode(self, tokens) -> str:
        """Retry output exhaustion or omitted numeric identifiers."""
        source = self.tokenizer.decode(tokens)
        if re.fullmatch(r"\s*\d[\d\s.,:;!?%/-]*", source):
            return source.strip()
        try:
            result = engine.translate_tokens(
                self.model, self.tokenizer, tokens, self.prefix
            )
            if identifiers(source) - identifiers(result):
                raise engine.DecodeLimit("A numeric identifier was omitted.")
            return result
        except engine.DecodeLimit:
            pieces = split_retry(tokens, self.tokenizer)
            return " ".join(self.translate(part) for part in pieces)


def split_retry(tokens, tokenizer) -> list:
    """Require each retry to shrink so repeated decoder failures terminate."""
    text = tokenizer.decode(tokens)
    cut = chunking.split_position(text)
    pieces = [
        tokenizer.encode(part.strip(), out_type=str)
        for part in (text[:cut], text[cut:])
    ]
    if not cut or any(not part or len(part) >= len(tokens) for part in pieces):
        raise config.AppError("The model could not finish this passage.")
    return pieces
