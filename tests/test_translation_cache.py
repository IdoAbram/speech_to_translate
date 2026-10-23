"""Remembered translations: hits, misses, eviction, and stale-key safety."""

import pytest

from speech_translate.translation import cache


def test_miss_then_hit():
    """Return nothing until a translation is stored, then return it."""
    store = cache.TranslationCache()
    assert store.get("Dzień dobry", "pl", "he") is None
    store.put("Dzień dobry", "pl", "he", "בוקר טוב")
    assert store.get("Dzień dobry", "pl", "he") == "בוקר טוב"


def test_languages_and_text_are_part_of_the_key():
    """Never reuse a result for another target, source, or edited text."""
    store = cache.TranslationCache()
    store.put("Dzień dobry", "pl", "he", "בוקר טוב")
    assert store.get("Dzień dobry", "pl", "en") is None
    assert store.get("Dzień dobry", "en", "he") is None
    assert store.get("Dzień dobry!", "pl", "he") is None


def test_line_endings_share_one_entry():
    """Treat Windows and Unix line endings as the same transcript."""
    store = cache.TranslationCache()
    store.put("a\r\nb", "pl", "en", "A\nB")
    assert store.get("a\nb", "pl", "en") == "A\nB"
    assert len(store) == 1


def test_least_recently_used_entry_is_evicted():
    """Keep memory bounded while preserving recently viewed results."""
    store = cache.TranslationCache(max_entries=2)
    store.put("one", "pl", "en", "1")
    store.put("two", "pl", "en", "2")
    store.get("one", "pl", "en")
    store.put("three", "pl", "en", "3")
    assert store.get("two", "pl", "en") is None
    assert store.get("one", "pl", "en") == "1"
    assert len(store) == 2


def test_rejects_empty_capacity():
    """A cache that can hold nothing is a configuration mistake."""
    with pytest.raises(ValueError):
        cache.TranslationCache(max_entries=0)
