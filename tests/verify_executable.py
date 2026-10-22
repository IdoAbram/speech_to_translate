"""Manually verify a relocated EXE with Unicode paths and no Python on PATH."""

import argparse
import json
import os
import pathlib
import shutil
import subprocess
import tempfile
import time

from speech_translate import config
from tests import helpers


def isolated_environment() -> dict:
    """Keep Windows essentials while excluding Python and project settings."""
    names = ("SystemRoot", "WINDIR", "TEMP", "TMP", "APPDATA", "LOCALAPPDATA")
    environment = {
        name: os.environ[name] for name in names if name in os.environ
    }
    windows = pathlib.Path(environment["SystemRoot"])
    environment["PATH"] = os.pathsep.join(
        (str(windows / "System32"), str(windows))
    )
    environment["QT_QPA_PLATFORM"] = "offscreen"
    return environment


def relocate(executable: pathlib.Path, portable: bool) -> pathlib.Path:
    """Copy release assets into a separate directory with a Unicode name."""
    kind = "portable-check" if portable else "standalone-check"
    destination = config.ROOT / ".downloads" / kind / "שירים"
    destination.mkdir(parents=True, exist_ok=True)
    if portable:
        shutil.copytree(executable.parent, destination, dirs_exist_ok=True)
    else:
        shutil.copy2(executable, destination / executable.name)
        assert not (destination / "models").exists()
    return destination / executable.name


def check_release(executable: pathlib.Path, portable: bool) -> dict:
    """Exercise MP3 decoding, detection, and every translation route."""
    copied = relocate(executable, portable)
    audio = copied.parent / "שיר בדיקה.mp3"
    helpers.encode_mp3(config.ROOT / "tests/fixtures/sample.wav", audio)
    report = copied.parent / "verification.json"
    started = time.monotonic()
    subprocess.run(
        [str(copied), "--self-test", str(report), "--audio", str(audio)],
        cwd=tempfile.gettempdir(),
        env=isolated_environment(),
        timeout=240,
        check=True,
    )
    result = json.loads(report.read_text(encoding="utf-8"))
    validate_result(result, portable)
    result["wall_seconds"] = round(time.monotonic() - started, 2)
    return result


def validate_result(result: dict, portable: bool) -> None:
    """Require actual frozen inference and embedded assets in the single EXE."""
    assert result["ok"] and result["frozen"] and result["language"] == "en"
    assert len(result["translations"]) == 6
    assert "meeting" in result["transcript"]
    if not portable:
        assert "_MEI" in result["models"]


def main(argv=None) -> int:
    """Save a reproducible release-check report beside the test artifacts."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("executable", type=pathlib.Path)
    parser.add_argument("--portable", action="store_true")
    args = parser.parse_args(argv)
    result = check_release(args.executable.resolve(), args.portable)
    kind = "portable" if args.portable else "standalone"
    report = config.ROOT / ".downloads" / f"{kind}-verified.json"
    report.write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"Verified {kind} release in {result['wall_seconds']} seconds.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
