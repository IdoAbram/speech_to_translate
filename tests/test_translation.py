"""All translation modules, with deterministic inputs and model doubles."""

import contextlib
import types
from unittest import mock

import pytest

from speech_translate import config
from speech_translate.translation import (
    chunking,
    engine,
    packages,
    service,
    tokenizers,
)
from tests import helpers

PAIRS = [(a, b) for a in config.LANGUAGES for b in config.LANGUAGES]


@pytest.mark.parametrize(("source", "target"), PAIRS)
def test_every_language_route(source, target):
    """Cover direct, pivoted, and same-language requests."""
    result = packages.route(source, target)
    if source == target:
        assert not result
    else:
        assert result[0][0] == source and result[-1][1] == target
        assert len(result) == 1


@pytest.mark.parametrize(
    "text",
    ["שלום עולם " * 100, "Zażółć! " * 100, "x" * 1000],
    ids=["hebrew", "polish", "unbroken"],
)
def test_chunking_never_truncates(text):
    """Split oversized Unicode inputs without dropping nonspace characters."""
    chunks = chunking.split_for_model(text, helpers.CharacterTokenizer(), 32)
    assert all(len(chunk) <= 32 for chunk in chunks)
    restored = "".join("".join(chunk) for chunk in chunks)
    assert "".join(restored.split()) == "".join(text.split())


def test_invalid_chunk_limits():
    """Reject a zero budget and an indivisible oversized token."""
    with pytest.raises(ValueError):
        chunking.split_for_model("hello", helpers.CharacterTokenizer(), 0)
    tokenizer = mock.Mock(encode=lambda *args, **kwargs: ["a", "b"])
    with pytest.raises(config.AppError):
        chunking.bounded_chunks("x", tokenizer, 1)


def test_empty_and_same_language():
    """Identity translation keeps every newline and needs no model."""
    text = "שלום\nשוב\n\nשלום\n"
    assert service.translate(text, "he", "he") == text
    with pytest.raises(config.AppError):
        service.translate(" ", "en", "pl")


def test_context_preserves_stanzas(tmp_path, monkeypatch):
    """Keep related lyric lines together and preserve repeated stanzas."""
    helpers.make_multilingual(tmp_path)
    monkeypatch.setattr(
        tokenizers,
        "MultilingualTokenizer",
        lambda *args: helpers.CharacterTokenizer(),
    )
    monkeypatch.setattr(
        engine, "open_engine", lambda path: contextlib.nullcontext(None)
    )
    monkeypatch.setattr(
        engine,
        "translate_tokens",
        lambda model, tok, tokens, prefix: "".join(tokens),
    )
    text = "שלום עולם\nשוב\n\nשוב\n"
    result = service.translate(text, "he", "pl", models_dir=tmp_path)
    assert result == "שלום עולם שוב\n\nשוב"


def test_decode_markers_and_prefix():
    """Remove model prefixes and literal SentencePiece spacing markers."""
    model = mock.Mock()
    model.translate_batch.return_value = [
        types.SimpleNamespace(hypotheses=[["tag", "Hello▁world"]])
    ]
    tokenizer = mock.Mock(decode=lambda tokens: "".join(tokens))
    assert (
        engine.translate_tokens(model, tokenizer, ["input"], "tag")
        == "Hello world"
    )
    assert model.translate_batch.call_args.kwargs["max_input_length"] == 0


@pytest.mark.parametrize("tokens", [[], ["x"] * engine.OUTPUT_LIMIT])
def test_reject_empty_or_truncated_translation(tokens):
    """Never silently return an empty or truncated translated line."""
    model = mock.Mock()
    model.translate_batch.return_value = [
        types.SimpleNamespace(hypotheses=[tokens])
    ]
    with pytest.raises(config.AppError):
        engine.translate_tokens(model, helpers.CharacterTokenizer(), ["in"], "")


def test_translation_engine_cleanup(tmp_path, monkeypatch):
    """Release a native model when processing fails."""
    import ctranslate2

    model = mock.Mock()
    monkeypatch.setattr(
        ctranslate2, "Translator", mock.Mock(return_value=model)
    )
    with pytest.raises(ValueError), engine.open_engine(tmp_path):
        raise ValueError("failed")
    model.unload_model.assert_called_once()
