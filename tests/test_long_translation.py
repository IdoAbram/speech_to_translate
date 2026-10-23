"""Long documents, passage context, output-budget recovery, and cancellation."""

import contextlib
import threading
from unittest import mock

import pytest

from speech_translate import config
from speech_translate.translation import (
    engine,
    packages,
    passages,
    service,
    tokenizers,
)
from tests import helpers


@pytest.fixture
def local_translation(tmp_path, monkeypatch):
    """Keep real orchestration while replacing only native inference."""
    helpers.make_multilingual(tmp_path)
    monkeypatch.setattr(
        tokenizers,
        "MultilingualTokenizer",
        lambda *args: helpers.CharacterTokenizer(),
    )
    monkeypatch.setattr(
        engine, "open_engine", lambda path: contextlib.nullcontext(None)
    )
    decoder = mock.Mock(
        side_effect=lambda model, tok, tokens, prefix: "".join(tokens)
    )
    monkeypatch.setattr(engine, "translate_tokens", decoder)
    return tmp_path, decoder


def test_long_multilingual_document_loses_no_words(local_translation):
    """Process over 40,000 characters with bounded inputs and no size error."""
    root, decoder = local_translation
    text = "\n\n".join(
        f"{i} שלום עולם\nZażółć gęślą jaźń. Keep the context."
        for i in range(1000)
    )
    updates = []
    result = service.translate(
        text,
        "he",
        "pl",
        models_dir=root,
        progress=lambda _, value: updates.append(value),
    )
    assert result.split() == text.split()
    assert result.count("\n\n") == 999
    assert all(len(call.args[2]) <= 256 for call in decoder.call_args_list)
    measured = [value for value in updates if value >= 0]
    assert measured == sorted(measured) and measured[-1] == 100


def test_lines_stay_aligned_and_choruses_are_cached(local_translation):
    """Translate each visual line once and retain every repeated chorus."""
    root, decoder = local_translation
    verse = "She put the book\non the table. It was a gift."
    output = service.translate(
        f"{verse}\n\n{verse}", "en", "he", models_dir=root
    )
    assert decoder.call_count == 2
    assert output.split("\n") == [*verse.split("\n"), "", *verse.split("\n")]


def limited_decoder(model, tokenizer, tokens, prefix):
    """Simulate the output-limit failure that previously rejected short text."""
    if len(tokens) > 12:
        raise engine.DecodeLimit("budget")
    return "".join(tokens)


def test_output_limit_retries_without_user_shortening(monkeypatch):
    """Recover by splitting smaller, retaining every source word."""
    monkeypatch.setattr(engine, "translate_tokens", limited_decoder)
    text = "This short text should never require the user to shorten it."
    output = passages.translate_chunk(
        None, helpers.CharacterTokenizer(), list(text), "", config.Operation()
    )
    assert output.split() == text.split()


def test_nonshrinking_retries_stop_and_cancellation_wins(monkeypatch):
    """Do not loop forever when the model cannot decode even one token."""
    decoder = mock.Mock(side_effect=engine.DecodeLimit("budget"))
    monkeypatch.setattr(engine, "translate_tokens", decoder)
    with pytest.raises(config.AppError, match="could not finish"):
        passages.translate_chunk(
            None, helpers.CharacterTokenizer(), ["x"], "", config.Operation()
        )
    cancel = threading.Event()
    cancel.set()
    with pytest.raises(config.Cancelled):
        passages.translate_chunk(
            None,
            helpers.CharacterTokenizer(),
            ["x"],
            "",
            config.Operation(cancel=cancel),
        )
    assert decoder.call_count == 1


def test_multilingual_assets_and_markers(tmp_path, monkeypatch):
    """Validate local files and reproduce the published NLLB token format."""
    import sentencepiece

    with pytest.raises(config.AppError, match="upgraded"):
        packages.multilingual_path(tmp_path)
    path = helpers.make_multilingual(tmp_path)
    assert packages.multilingual_path(tmp_path) == path
    processor = helpers.CharacterTokenizer()
    monkeypatch.setattr(
        sentencepiece, "SentencePieceProcessor", lambda **kw: processor
    )
    tokenizer = tokenizers.MultilingualTokenizer(path, "he")
    assert tokenizer.prepare(tokenizer.encode("שלום")) == [
        "heb_Hebr",
        *"שלום",
        "</s>",
    ]
    assert tokenizer.decode([*"שלום"]) == "שלום"


def test_omitted_identifier_retries_and_reuses_fragments(monkeypatch):
    """Never silently omit a heading number while translating a long stanza."""
    decoder = mock.Mock(side_effect=omit_heading)
    monkeypatch.setattr(engine, "translate_tokens", decoder)
    translator = passages.PassageTranslator(
        None, helpers.CharacterTokenizer(), "", config.Operation()
    )
    first = translator.translate(list("Chapter 1001. I came home."))
    second = translator.translate(list("Chapter 1002. I came home."))
    assert "1001" in first and "1002" in second
    body_calls = [
        call
        for call in decoder.call_args_list
        if "".join(call.args[2]) == "I came home."
    ]
    assert len(body_calls) == 1
    assert passages.identifiers("1,001 and 2 002") == {"1001", "2002"}
    assert passages.identifiers("פרק1001") == {"1001"}
    assert translator.translate(list("1003")) == "1003"
    assert translator.translate(list("1003.")) == "1003."


def omit_heading(model, tokenizer, tokens, prefix):
    """Reproduce a real model omission when a heading shares a passage."""
    text = "".join(tokens)
    return (
        "I came home."
        if text.startswith("Chapter") and "home" in text
        else text
    )
