"""Keep function size and module-level documentation from regressing."""

import ast

from speech_translate import config


def project_sources():
    """List owned Python source, excluding virtual environments and models."""
    paths = [
        config.ROOT / name
        for name in (
            "app.py",
            "setup_models.py",
            "build_windows.py",
            "build_support.py",
        )
    ]
    for folder in ("speech_translate", "tests"):
        paths.extend((config.ROOT / folder).rglob("*.py"))
    return paths


def test_all_functions_are_at_most_twenty_lines():
    """Count physical lines, including decorators and docstrings."""
    violations = []
    for path in project_sources():
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                starts = [node.lineno] + [d.lineno for d in node.decorator_list]
                length = node.end_lineno - min(starts) + 1
                if length > 20:
                    violations.append(f"{path.name}:{node.name}: {length}")
    assert not violations, "\n".join(violations)


def test_modules_have_documentation():
    """Keep each small module's responsibility explicit."""
    for path in project_sources():
        assert ast.get_docstring(ast.parse(path.read_text(encoding="utf-8")))
