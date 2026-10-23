"""Command-line interfaces and thin launch scripts."""

import runpy
from unittest import mock

import pytest

import setup_models
from speech_translate import cli, config, gui, speech, translation
from speech_translate.installation import cli as setup_cli


def test_transcription_command(song, tmp_path, monkeypatch):
    """Write a speech result with its lyric spacing preserved."""
    result = speech.Transcript("en", (speech.Segment(0, 1, "Hello"),), 1)
    monkeypatch.setattr(speech, "transcribe", lambda *args: result)
    output = tmp_path / "transcript.txt"
    args = ["transcribe", str(song), "--language", "en"]
    assert cli.main([*args, "--output", str(output)]) == 0
    assert output.read_text(encoding="utf-8-sig") == "Hello"


def test_translation_command(tmp_path, monkeypatch, capsys):
    """Read UTF-8 BOM source files and export both script and spacing."""
    source, target = tmp_path / "source.txt", tmp_path / "translated.txt"
    source.write_text("Hello\n\nAgain", encoding="utf-8-sig")
    monkeypatch.setattr(translation, "translate", fallback_translation)
    arguments = ["translate", str(source), "--source", "en", "--target", "he"]
    assert cli.main([*arguments, "--output", str(target)]) == 0
    assert target.read_text(encoding="utf-8-sig") == "Hello\n\nAgain"
    assert "offline model" in capsys.readouterr().err


def fallback_translation(text, *args, notice):
    """Echo the text and report an offline fallback like the service does."""
    notice("Groq was unavailable. Used the offline model.")
    return text


def test_cli_preserves_existing_files(song):
    """Reject output paths that would overwrite source data."""
    with pytest.raises(SystemExit) as error:
        cli.main(
            ["transcribe", str(song), "--language", "en", "--output", str(song)]
        )
    assert error.value.code == 2
    assert song.read_bytes() == b"fixture audio"


def test_cli_missing_file(tmp_path, capsys):
    """Return a nonzero status with a useful error for missing input."""
    args = [
        "translate",
        str(tmp_path / "missing.txt"),
        "--source",
        "he",
        "--target",
        "pl",
    ]
    assert cli.main([*args, "--output", str(tmp_path / "out.txt")]) == 1
    assert "Error:" in capsys.readouterr().err


@pytest.mark.parametrize("script", ["app.py", "setup_models.py"])
def test_script_entrypoints(script, monkeypatch):
    """Launch scripts delegate to their package entry points."""
    monkeypatch.setattr(gui, "main", lambda: 0)
    monkeypatch.setattr(setup_cli, "main", lambda: 0)
    with pytest.raises(SystemExit) as error:
        runpy.run_path(str(config.ROOT / script), run_name="__main__")
    assert error.value.code == 0
    assert callable(setup_models.main)


def test_module_entrypoint(monkeypatch):
    """Keep python -m speech_translate wired to the tested CLI."""
    monkeypatch.setattr(cli, "main", lambda: 0)
    with pytest.raises(SystemExit) as error:
        runpy.run_module("speech_translate", run_name="__main__")
    assert error.value.code == 0


def test_gui_entrypoint(monkeypatch):
    """Configure and show the desktop before entering the event loop."""
    application = mock.Mock()
    application.exec.return_value = 0
    window = mock.Mock()
    with monkeypatch.context() as patcher:
        patcher.setattr(gui.QtWidgets, "QApplication", lambda args: application)
        patcher.setattr(gui, "Window", lambda: window)
        assert gui.main() == 0
    window.showFullScreen.assert_called_once()
    application.exec.assert_called_once()
