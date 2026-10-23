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
    answer(urlopen, reply(["x"]), reply(["y"]), reply(["z"]))
    with pytest.raises(config.AppError, match="line by line"):
        groq.translate_lyrics(SONG, "pl", "he", "k", config.Operation())


@pytest.mark.parametrize(
    ("status", "message"),
    [(401, "groq_key.txt"), (404, "not available"), (400, "another")],
)
def test_http_errors_are_explained(urlopen, monkeypatch, status, message):
    """Turn key and model errors into actionable messages."""
    monkeypatch.setattr(groq, "KEY_FILE", "groq_key.txt")
    urlopen.side_effect = urllib.error.HTTPError("u", status, "", {}, None)
    with pytest.raises(config.AppError, match=message):
        groq.translate_lyrics(SONG, "pl", "en", "k", config.Operation())


def test_broken_json_is_retried(urlopen):
    """Groq sometimes rejects its own JSON; another attempt usually works."""
    details = io.BytesIO(b'{"error": {"code": "json_validate_failed"}}')
    broken = urllib.error.HTTPError("u", 400, "", {}, details)
    answer(urlopen, reply(["a", "b", "c"]))
    urlopen.side_effect = [broken, urlopen.return_value]
    result = groq.translate_lyrics(SONG, "pl", "en", "k", config.Operation())
    assert result.split("\n") == ["a", "b", "", "c", ""]


def limited(seconds):
    """Build Groq's 429 answer with its suggested pause."""
    return urllib.error.HTTPError(
        "u", 429, "", {"retry-after": str(seconds)}, None
    )


def test_rate_limit_is_waited_out(urlopen, monkeypatch):
    """Pause for the free plan's reset instead of failing the song."""
    sleeps, updates = [], []
    monkeypatch.setattr(groq.time, "sleep", sleeps.append)
    clock = iter(range(0, 100))
    monkeypatch.setattr(groq.time, "monotonic", lambda: next(clock))
    answer(urlopen, reply(["a", "b", "c"]))
    urlopen.side_effect = [limited(3), urlopen.return_value]
    operation = config.Operation(lambda message, _: updates.append(message))
    result = groq.translate_lyrics(SONG, "pl", "en", "k", operation)
    assert result.split("\n") == ["a", "b", "", "c", ""]
    assert sleeps and any("waiting" in message for message in updates)


def test_daily_limit_fails_fast(urlopen):
    """A pause longer than a minute means the daily cap; do not hang."""
    urlopen.side_effect = limited(3600)
    with pytest.raises(config.AppError, match="daily limit"):
        groq.translate_lyrics(SONG, "pl", "en", "k", config.Operation())


def echo_lines(request, timeout):
    """Answer each request by upper-casing exactly the lines it sent."""
    prompt = json.loads(request.data)["messages"][0]["content"]
    lines = json.loads(prompt[prompt.index("\n\n[") + 2 :])
    reply_body = reply([line.upper() for line in lines])
    return mock.MagicMock(__enter__=mock.Mock(return_value=reply_body))


def test_long_song_is_sent_in_parts(urlopen):
    """Forty lines go out as 15 + 15 + 10 and come back in order."""
    urlopen.side_effect = echo_lines
    song = "\n".join(f"wers {index}" for index in range(40))
    result = groq.translate_lyrics(song, "pl", "he", "k", config.Operation())
    assert result == song.upper()
    sizes = [
        len(json.loads(call.args[0].data)["messages"][0]["content"])
        for call in urlopen.call_args_list
    ]
    assert len(sizes) == 3


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
    monkeypatch.setenv("GROQ_MODEL", "llama-test")
    answer(urlopen, reply(["a", "b", "c"]))
    result = service.translate(SONG, "pl", "he", models_dir="missing")
    assert result.split("\n") == ["a", "b", "", "c", ""]
    body = json.loads(urlopen.call_args.args[0].data)
    assert body["model"] == "llama-test"
    assert body["response_format"] == {"type": "json_object"}


@pytest.mark.parametrize(
    "model", ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
)
def test_strict_schema_for_supported_models(model):
    """Groq rejects strict schemas on models that do not support them."""
    assert groq.response_format(model)["json_schema"]["strict"] is True
