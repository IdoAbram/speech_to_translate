"""A lightweight SentencePiece adapter for the multilingual model."""

import pathlib

from speech_translate.translation import packages


class MultilingualTokenizer:
    """Encode NLLB-200 text with the same language markers as its tokenizer."""

    def __init__(self, path: pathlib.Path, source: str):
        """Load only SentencePiece; Transformers is not needed at runtime."""
        import sentencepiece

        self.processor = sentencepiece.SentencePieceProcessor(
            model_file=str(path / "sentencepiece.bpe.model")
        )
        self.source = packages.language_token(source)

    def encode(self, text: str, out_type=str) -> list[str]:
        """Return content tokens; language markers are added at inference."""
        return self.processor.encode(text, out_type=out_type)

    def decode(self, tokens: list[str]) -> str:
        """Restore text from predicted content tokens."""
        return self.processor.decode(tokens)

    def prepare(self, tokens: list[str]) -> list[str]:
        """Add NLLB-200's source language and end-of-sequence markers."""
        return [self.source, *tokens, "</s>"]
