"""Check native libraries, widgets, and models inside a frozen executable."""

import argparse
import json
import pathlib
import sys
import time

from PySide6 import QtWidgets

from speech_translate import config, speech, translation
from speech_translate.gui import theme
from speech_translate.gui.window import Window

EXAMPLES = {
    "en": "The meeting starts tomorrow at nine in the morning.",
    "he": "הפגישה מתחילה מחר בשעה תשע בבוקר.",
    "pl": "Spotkanie zaczyna się jutro o dziewiątej rano.",
}


def check_translations() -> list:
    """Load the bundled model and execute every supported direction."""
    results = []
    for source in config.LANGUAGES:
        for target in config.LANGUAGES:
            if source != target:
                text = translation.translate(EXAMPLES[source], source, target)
                if not text.strip():
                    raise config.AppError("Empty packaged translation")
                results.append(
                    {"source": source, "target": target, "text": text}
                )
    return results


def check_desktop() -> None:
    """Construct the real themed interface and render its initial layout."""
    application = QtWidgets.QApplication.instance() or QtWidgets.QApplication(
        []
    )
    application.setStyleSheet(theme.STYLESHEET)
    window = Window()
    window.showFullScreen()
    application.processEvents()
    if not window.isFullScreen():
        raise config.AppError("Fullscreen startup failed")
    window.close()
    application.processEvents()


def run_checks(audio: pathlib.Path | None) -> dict:
    """Check relocatable model paths, actual inference, and the Qt runtime."""
    started = time.monotonic()
    config.offline_mode()
    check_desktop()
    result = {
        "frozen": bool(getattr(sys, "frozen", False)),
        "models": str(config.MODELS),
        "translations": check_translations(),
    }
    if audio:
        transcript = speech.transcribe(audio)
        result["transcript"] = transcript.text
        result["language"] = transcript.language
    result["seconds"] = round(time.monotonic() - started, 2)
    result["ok"] = True
    return result


def main(argv=None) -> int:
    """Write a JSON result so a windowed executable can be checked in CI."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=pathlib.Path)
    parser.add_argument("--audio", type=pathlib.Path)
    args = parser.parse_args(argv)
    try:
        result = run_checks(args.audio)
    except Exception as error:
        result = {"ok": False, "error": str(error)}
    args.output.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return 0 if result["ok"] else 1
