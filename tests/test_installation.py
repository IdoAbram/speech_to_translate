"""Downloader, archive validation, pinned models, and setup orchestration."""

import io
from unittest import mock

import pytest

from speech_translate.installation import (
    cli,
    downloads,
    multilingual,
    speech_models,
)


def response(data=b"download", length=None):
    """Create a streaming HTTP response without network access."""
    result = io.BytesIO(data)
    result.headers = {
        "Content-Length": str(len(data) if length is None else length)
    }
    return result


def test_atomic_download(tmp_path, monkeypatch):
    """Rename a complete response and leave no partial model file."""
    monkeypatch.setattr(
        downloads.urllib.request, "urlopen", lambda *args, **kwargs: response()
    )
    path = tmp_path / "model.bin"
    downloads.download("https://example.com/model", path)
    assert path.read_bytes() == b"download"
    assert not path.with_suffix(".bin.part").exists()


def test_truncated_download_keeps_existing_file(tmp_path, monkeypatch):
    """Do not replace an installed model with a truncated transfer."""
    path = tmp_path / "model.bin"
    path.write_bytes(b"original")
    monkeypatch.setattr(
        downloads.urllib.request,
        "urlopen",
        lambda *args, **kwargs: response(b"x", 10),
    )
    with pytest.raises(OSError, match="Incomplete"):
        downloads.download("https://example.com/model", path)
    assert path.read_bytes() == b"original"


def test_json_and_manifest(tmp_path, monkeypatch):
    """Read remote JSON and preserve existing model provenance."""
    monkeypatch.setattr(
        downloads.urllib.request,
        "urlopen",
        lambda *args, **kwargs: response(b'{"sha": "revision"}'),
    )
    assert downloads.fetch_json("https://example.com/info")["sha"] == "revision"
    path = tmp_path / "manifest.json"
    assert downloads.read_json(path) == {}
    cli.record(path, "first", {"version": "1"})
    cli.record(path, "second", {"version": "2"})
    cli.record(path, "first", {})
    assert set(downloads.read_json(path)) == {"first", "second"}


def test_speech_revision_retry(tmp_path, monkeypatch):
    """Use the pinned revision's file inventory on interrupted retries."""
    info = {"sha": "pinned", "siblings": []}
    fetch = mock.Mock(return_value=info)
    monkeypatch.setattr(downloads, "fetch_json", fetch)
    speech_models.repository_info(tmp_path, "owner/model")
    speech_models.repository_info(tmp_path, "owner/model")
    assert fetch.call_args.args[0].endswith("/revision/pinned")


def write_download(url, destination):
    """Stand in for model bytes without depending on a remote repository."""
    destination.write_bytes(b"fixture")


def test_install_speech_and_reuse(tmp_path, monkeypatch):
    """Download missing speech files once and validate the completed model."""
    info = {
        "sha": "fixed",
        "siblings": [{"rfilename": name} for name in speech_models.FILES],
    }
    monkeypatch.setattr(downloads, "fetch_json", lambda url: info)
    monkeypatch.setattr(downloads, "download", write_download)
    assert speech_models.install(tmp_path, "small")["revision"] == "fixed"
    assert speech_models.install(tmp_path, "small") == {}


def test_setup_cli_installs_every_package(tmp_path, monkeypatch):
    """Exercise the installer CLI without downloading large model files."""
    monkeypatch.setattr(
        speech_models, "install", lambda *args: {"revision": "x"}
    )
    install = mock.Mock(return_value={"sha256": "digest"})
    monkeypatch.setattr(multilingual, "install", install)
    assert cli.main(["--models-dir", str(tmp_path)]) == 0
    assert install.call_count == 1
    assert len(downloads.read_json(tmp_path / "manifest.json")) == 2


def test_setup_cli_reports_failure(tmp_path, monkeypatch):
    """Return a clear failure status when installation cannot proceed."""
    install = mock.Mock(side_effect=OSError("offline"))
    monkeypatch.setattr(speech_models, "install", install)
    assert cli.main(["--models-dir", str(tmp_path)]) == 1
