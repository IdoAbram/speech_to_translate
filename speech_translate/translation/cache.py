"""Remember finished translations so switching back to a language is instant."""

import collections

MAX_ENTRIES = 32


class TranslationCache:
    """A small least-recently-used store of finished translations.

    Entries are keyed by the exact source text and both language codes, so
    editing the transcript or changing a language never reuses a stale
    result.
    """

    def __init__(self, max_entries: int = MAX_ENTRIES):
        if max_entries < 1:
            raise ValueError("A translation cache needs at least one entry.")
        self._entries = collections.OrderedDict()
        self._max_entries = max_entries

    def __len__(self) -> int:
        return len(self._entries)

    @staticmethod
    def key(text: str, source: str, target: str) -> tuple[str, str, str]:
        """Treat Windows and Unix line endings as the same source text."""
        return text.replace("\r\n", "\n"), source, target

    def get(self, text: str, source: str, target: str) -> str | None:
        """Return a remembered translation, or None if it was never stored.

        Args:
            text: The source text exactly as it was translated.
            source: The source language code.
            target: The target language code.

        Returns:
            The earlier translation, or None on a cache miss.
        """
        key = self.key(text, source, target)
        if key not in self._entries:
            return None
        self._entries.move_to_end(key)
        return self._entries[key]

    def put(self, text: str, source: str, target: str, result: str) -> None:
        """Store a translation, evicting the least recently used entry."""
        key = self.key(text, source, target)
        self._entries[key] = result
        self._entries.move_to_end(key)
        while len(self._entries) > self._max_entries:
            self._entries.popitem(last=False)
