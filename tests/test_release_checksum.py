"""Exercise the PowerShell integrity gate used before testing and deployment."""

import hashlib
import shutil
import subprocess

import pytest

from speech_translate import config

SHELL = shutil.which("pwsh") or shutil.which("powershell")
pytestmark = pytest.mark.skipif(not SHELL, reason="PowerShell is required")


def verify(directory):
    """Run the actual release script without interpreting shell input."""
    script = config.ROOT / ".github/scripts/verify-package.ps1"
    return subprocess.run(
        [
            SHELL,
            "-NoProfile",
            "-NonInteractive",
            "-File",
            str(script),
            "-Directory",
            str(directory),
        ],
        capture_output=True,
        timeout=30,
        check=False,
    )


@pytest.fixture
def candidate(tmp_path):
    """Create a small candidate with the same checksum format as CI."""
    payload = b"synthetic executable fixture"
    (tmp_path / "SongWords.exe").write_bytes(payload)
    checksum = hashlib.sha256(payload).hexdigest() + "  SongWords.exe\n"
    (tmp_path / "SHA256SUMS.txt").write_text(checksum, encoding="utf-8")
    return tmp_path


def test_original_candidate_passes(candidate):
    """Allow a release whose bytes match the recorded build checksum."""
    assert verify(candidate).returncode == 0


@pytest.mark.parametrize("damage", ["changed", "missing", "malformed"])
def test_damaged_candidate_blocks_deployment(candidate, damage):
    """Reject altered files, missing executables, and invalid manifests."""
    if damage == "changed":
        (candidate / "SongWords.exe").write_bytes(b"corrupted executable")
    elif damage == "missing":
        (candidate / "SongWords.exe").unlink()
    else:
        (candidate / "SHA256SUMS.txt").write_text("not a checksum")
    assert verify(candidate).returncode != 0
