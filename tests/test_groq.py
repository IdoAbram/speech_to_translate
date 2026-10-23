"""Groq lyric translation with a fake HTTP layer; no network is used."""

import io
import json
import urllib.error
from unittest import mock

import pytest

from speech_translate import config
from speech_translate.translation import groq, service

SONG = "Tylko jedno w głowie mam\nKoksu pięć gram\n\nW krainę zapomnienia\n"


def reply(lines):
    """Build a chat completion whose content is the strict JSON object."""
    content = json.dumps({"lines": lines}, ensure_ascii=False)
    body = {"choices": [{"message": {"content": content}}]}
    return io.BytesIO(json.dumps(body).encode("utf-8"))


@pytest.fixture
def urlopen(monkeypatch):
    """Replace the HTTP call so each test decides what Groq answers."""
    fake = mock.MagicMock()
    monkeypatch.setattr(groq.urllib.request, "urlopen", fake)
    return fake


def answer(urlopen, *replies):
    """Queue Groq replies for successive requests."""
    urlopen.return_value.__enter__.side_effect = list(replies)


def test_keeps_lines_and_stanzas(urlopen):
    """Blank lines stay local; line N of the result matches line N."""
    answer(urlopen, reply(["Only one thing", "Five grams of coke", "Oblivion"]))
    result = groq.translate_lyrics(SONG, "pl", "en", "k", config.Operation())
    assert result == "Only one thing\nFive grams of coke\n\nOblivion\n"
    request = urlopen.call_args.args[0]
    assert request.get_header("Authorization") == "Bearer k"
    body = json.loads(request.data)
    assert body["model"] == groq.DEFAULT_MODEL
    assert "Koksu pięć gram" in body["messages"][0]["content"]


def test_retries_when_line_count_differs(urlopen):
    """Ask again once if Groq merges lines, then give up clearly."""
    answer(urlopen, reply(["merged"]), reply(["a", "b", "c"]))
    result = groq.translate_lyrics(SONG, "pl", "he", "k", config.Operation())
    assert result.split("\n") == ["a", "b", "", "c", ""]
    answer(urlopen, reply(["x"]), reply(["y"]))
    with pytest.raises(config.AppError, match="number of lines"):
        groq.translate_lyrics(SONG, "pl", "he", "k", config.Operation())


@pytest.mark.parametrize(
    ("status", "message"),
    [(429, "free limit"), (401, "groq_key.txt"), (404, "retired")],
)
def test_http_errors_are_explained(urlopen, monkeypatch, status, message):
    """Turn quota, key, and model errors into actionable messages."""
    monkeypatch.setattr(groq, "KEY_FILE", "groq_key.txt")
    urlopen.side_effect = urllib.error.HTTPError("u", status, "", {}, None)
    with pytest.raises(config.AppError, match=message):
        groq.translate_lyrics(SONG, "pl", "en", "k", config.Operation())


def test_offline_computer_gets_clear_error(urlopen):
    """Report a missing connection instead of a stack trace."""
    urlopen.side_effect = urllib.error.URLError("offline")
    with pytest.raises(config.AppError, match="internet"):
        groq.translate_lyrics(SONG, "pl", "en", "k", config.Operation())


@pytest.mark.parametrize(
    "content",
    [None, "not json", '["no", "object"]', '{"lines": "text"}'],
    ids=["empty", "unreadable", "array", "not-a-list"],
)
def test_bad_answers_are_rejected(content):
    """Never show an empty or garbled answer as a translation."""
    response = {"choices": [{"message": {"content": content}}]}
    with pytest.raises(config.AppError):
        groq.parse_lines(response)


def test_key_from_environment_or_file(tmp_path, monkeypatch):
    """Prefer the environment and fall back to the file beside the app."""
    monkeypatch.setattr(groq, "KEY_FILE", "groq_key.txt")
    assert groq.api_key(tmp_path) == ""
    (tmp_path / "groq_key.txt").write_text(" file-key \n", encoding="utf-8")
    assert groq.api_key(tmp_path) == "file-key"
    monkeypatch.setenv("GROQ_API_KEY", "env-key")
    assert groq.api_key(tmp_path) == "env-key"


def test_service_prefers_groq_when_configured(urlopen, monkeypatch):
    """Use Groq with a key and never load the offline model."""
    monkeypatch.setenv("GROQ_API_KEY", "k")
    monkeypatch.setenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    answer(urlopen, reply(["a", "b", "c"]))
    result = service.translate(SONG, "pl", "he", models_dir="missing")
    assert result.split("\n") == ["a", "b", "", "c", ""]
    assert json.loads(urlopen.call_args.args[0].data)["model"].startswith(
        "llama"
    )
