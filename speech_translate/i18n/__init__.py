"""Interface language: English by default, Hebrew for the desktop app.

Messages are written in English with named placeholders and looked up in a
catalog when shown, so the command line and tests stay English while the
desktop app speaks Hebrew. A test checks that every message has a Hebrew
translation with the same placeholders.
"""

from speech_translate.i18n import hebrew

CATALOGS = {"en": {}, "he": hebrew.MESSAGES}
_current = {"language": "en"}


def set_language(code: str) -> None:
    """Choose the language for every message shown from now on."""
    if code not in CATALOGS:
        raise ValueError(f"Unsupported interface language: {code}")
    _current["language"] = code


def right_to_left() -> bool:
    """Return whether the interface language is written right to left."""
    return _current["language"] == "he"


def tr(message: str, **values) -> str:
    """Translate an English message template, then fill its placeholders.

    Args:
        message: English text, with placeholders such as {error}.
        **values: Values for the placeholders.

    Returns:
        The message in the current interface language.
    """
    template = CATALOGS[_current["language"]].get(message, message)
    return template.format(**values) if values else template
