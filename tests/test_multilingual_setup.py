"""Model conversion isolation, reusable assets, and frozen build inputs."""

from unittest import mock

import pytest

import build_support
import build_windows
from speech_translate import config
from speech_translate.installation import conversion, downloads, multilingual
from tests import helpers


def test_source_download_pins_revision(tmp_path, monkeypatch):
    """Keep setup downloads at one revision and reuse completed files."""
    info = {
        "sha": "fixed",
        "siblings": [{"rfilename": name} for name in multilingual.FILES],
    }
    monkeypatch.setattr(downloads, "fetch_json", lambda url: info)
    fetch = mock.Mock(side_effect=lambda url, path: path.write_bytes(b"model"))
    monkeypatch.setattr(downloads, "download", fetch)
    assert multilingual.fetch_source(tmp_path) == info
    multilingual.fetch_source(tmp_path)
    assert fetch.call_count == len(multilingual.FILES)
    assert "/resolve/fixed/" in fetch.call_args.args[0]


def test_multilingual_install_and_reuse(tmp_path, monkeypatch):
    """Reuse valid conversion output and record its exact source revision."""
    monkeypatch.setattr(config, "ROOT", tmp_path)
    source = tmp_path / ".downloads" / "nllb-source"
    source.mkdir(parents=True)
    for name in ("sentencepiece.bpe.model", "README.md"):
        (source / name).write_bytes(b"fixture")
    monkeypatch.setattr(
        multilingual, "fetch_source", lambda path: {"sha": "fixed"}
    )
    monkeypatch.setattr(
        conversion,
        "convert",
        lambda *args: helpers.make_multilingual(tmp_path / "models"),
    )
    entry = multilingual.install(tmp_path / "models")
    assert entry["revision"] == "fixed" and entry["quantization"] == "int8"
    assert multilingual.install(tmp_path / "models") == {}


def test_converter_uses_separate_venv(tmp_path, monkeypatch):
    """Never install large converter dependencies into the desktop runtime."""
    monkeypatch.setattr(config, "ROOT", tmp_path)
    run = mock.Mock()
    monkeypatch.setattr(conversion.subprocess, "run", run)
    executable = conversion.prepare()
    assert ".model-venv" in str(executable)
    assert run.call_count == 2 and run.call_args.kwargs["check"]
    monkeypatch.setattr(conversion, "prepare", lambda: executable)
    conversion.convert(tmp_path / "source", tmp_path / "output")
    args = run.call_args.args[0]
    assert "--quantization" in args and "int8" in args
    assert run.call_args.kwargs["env"]["HF_HUB_OFFLINE"] == "1"


@pytest.mark.parametrize("single_file", [True, False])
def test_build_contains_models_and_python(tmp_path, monkeypatch, single_file):
    """Build each package with verified local assets and no PyTorch runtime."""
    monkeypatch.setattr(config, "ROOT", tmp_path)
    monkeypatch.setattr(config, "MODELS", tmp_path / "models")
    asset = helpers.make_multilingual(config.MODELS)
    monkeypatch.setattr(build_windows, "model_assets", lambda: [asset])
    monkeypatch.setattr(build_support, "data_options", lambda: [])
    for name in ("README.md", "LICENSE", "THIRD_PARTY_NOTICES.md"):
        (tmp_path / name).write_text("Read me")
    run = mock.Mock()
    monkeypatch.setattr(build_windows.subprocess, "run", run)
    output = build_windows.build(single_file)
    args = run.call_args.args[0]
    assert "PyInstaller" in args and "torch" in args
    if single_file:
        assert "--onefile" in args and "--add-data" in args
        assert output.suffix == ".exe"
    else:
        assert (output / "models/translation/nllb/model/model.bin").is_file()
