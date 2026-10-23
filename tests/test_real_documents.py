"""Opt-in checks of meaning and long documents with actual local weights."""

import os

import pytest

from speech_translate import translation
from tests import quality_cases

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(
        os.getenv("RUN_MODEL_TESTS") != "1", reason="Local model opt-in"
    ),
]


@pytest.mark.parametrize("source", ["he", "pl"])
def test_related_sentences_keep_key_meaning(source):
    """Require the letter, table, summer, and shared memory to survive."""
    result = translation.translate(quality_cases.CONTEXT[source], source, "en")
    words = result.lower()
    assert all(
        word in words for word in ("letter", "table", "summer", "together")
    )


def test_real_long_document_retains_every_chapter():
    """Translate over 5,000 words without truncating early or late passages."""
    text = quality_cases.long_document()
    assert len(text.split()) > 5000
    result = translation.translate(text, "en", "he")
    stanzas = result.split("\n\n")
    assert len(stanzas) == 100
    for number, stanza in zip(range(1001, 1101), stanzas):
        assert str(number) in stanza
        assert len(stanza.split()) > 20
