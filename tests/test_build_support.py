"""License collection and documentation inclusion in frozen packages."""

import pathlib
import types

import build_support
from speech_translate import config


def test_package_notices_are_copied(tmp_path, monkeypatch):
    """Copy distribution notices while ignoring ordinary package code."""
    license_file = tmp_path / "LICENSE.txt"
    license_file.write_text("License terms")
    distribution = types.SimpleNamespace(
        files=[pathlib.Path("LICENSE.txt"), pathlib.Path("module.py")],
        locate_file=lambda item: tmp_path / item,
    )
    monkeypatch.setattr(
        build_support.importlib.metadata,
        "distribution",
        lambda name: distribution,
    )
    destination = tmp_path / "output"
    build_support.copy_distribution("example", destination)
    assert (destination / "example/LICENSE.txt").read_text() == "License terms"


def test_build_documentation_options(tmp_path, monkeypatch):
    """Include model licenses, dependency notices, and user documentation."""
    monkeypatch.setattr(config, "ROOT", tmp_path)
    (tmp_path / "requirements.lock.txt").write_text("# Runtime\nexample==1\n")
    licenses = tmp_path / "licenses"
    licenses.mkdir()
    (licenses / "model.txt").write_text("Model terms")
    calls = []
    monkeypatch.setattr(
        build_support, "copy_distribution", lambda *args: calls.append(args)
    )
    options = build_support.data_options()
    assert calls[0][0] == "example"
    assert options.count("--add-data") == 4
    assert (tmp_path / "build/licenses/model.txt").is_file()
