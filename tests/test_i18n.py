"""Every interface message has a Hebrew translation with matching fields."""

import ast
import string

import pytest

from speech_translate import config, i18n
from speech_translate.i18n import hebrew
from tests import test_conventions


def placeholders(text: str) -> set[str]:
    """Return the named fields of a message template."""
    return {name for _, name, _, _ in string.Formatter().parse(text) if name}


def constants(tree: ast.Module) -> dict[str, str]:
    """Map module-level names to the message templates they hold."""
    found = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(
            node.value, ast.Constant
        ):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    found[target.id] = node.value.value
    return found


def is_translation(node: ast.AST) -> bool:
    """Recognize a call to i18n.tr with at least one argument."""
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "tr"
        and bool(node.args)
    )


def messages() -> set[str]:
    """Collect every template passed to i18n.tr in the application."""
    found = set(config.LANGUAGES.values())
    for path in test_conventions.project_sources():
        if "speech_translate" not in path.parts:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names = constants(tree)
        for node in filter(is_translation, ast.walk(tree)):
            argument = node.args[0]
            if isinstance(argument, ast.Constant):
                found.add(argument.value)
            elif isinstance(argument, ast.Name) and argument.id in names:
                found.add(names[argument.id])
    return found


def test_every_message_has_hebrew():
    """No English text can reach the Hebrew interface."""
    missing = sorted(messages() - hebrew.MESSAGES.keys())
    assert not missing, "\n".join(missing)


def test_no_unused_hebrew_entries():
    """Remove catalog entries whose English message no longer exists."""
    unused = sorted(hebrew.MESSAGES.keys() - messages())
    assert not unused, "\n".join(unused)


@pytest.mark.parametrize("english", sorted(hebrew.MESSAGES))
def test_placeholders_match(english):
    """A Hebrew message fills in exactly the same values."""
    assert placeholders(hebrew.MESSAGES[english]) == placeholders(english)


def test_switching_languages():
    """English by default, Hebrew on request, with values filled in."""
    assert i18n.tr("Translation ready.") == "Translation ready."
    assert not i18n.right_to_left()
    i18n.set_language("he")
    assert i18n.right_to_left()
    assert i18n.tr("Translation ready.") == "התרגום מוכן."
    assert "3" in i18n.tr("Translating passage 1 of {total}…", total=3)
    assert config.language_name("pl") == "פולנית"
    with pytest.raises(ValueError):
        i18n.set_language("fr")
