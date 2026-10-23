"""Online lyric translation with the free Groq API.

The whole song is sent in one request so the model sees full context, such
as slang that only makes sense across lines. A strict JSON schema makes the
model answer with a list of lines, and the app checks that it returned one
translation per non-empty source line, which keeps subtitles aligned.
"""

import json
import os
import urllib.error
import urllib.request

from speech_translate import config

KEY_FILE = "groq_key.txt"
DEFAULT_MODEL = "openai/gpt-oss-120b"
API_URL = "https://api.groq.com/openai/v1/chat/completions"
TIMEOUT_SECONDS = 120
ATTEMPTS = 3
# Models that accept strict JSON schemas, per Groq's structured-output docs.
STRICT_SCHEMA_MODELS = ("openai/gpt-oss", "qwen/qwen3.8", "meta-models/muse")
SCHEMA = {
    "type": "object",
    "properties": {"lines": {"type": "array", "items": {"type": "string"}}},
    "required": ["lines"],
    "additionalProperties": False,
}


class BadReply(config.AppError):
    """Groq produced a malformed answer that another attempt may fix."""


def api_key(root=config.ROOT) -> str:
    """Return the Groq key from the environment or the local key file.

    Args:
        root: Folder that may contain the key file next to the app.

    Returns:
        The key, or an empty string when Groq is not configured.
    """
    key = os.environ.get("GROQ_API_KEY", "").strip()
    path = root / KEY_FILE
    if not key and path.is_file():
        key = path.read_text(encoding="utf-8-sig").strip()
    return key


def translate_lyrics(text, source, target, key, operation) -> str:
    """Translate a whole song while keeping its exact line layout.

    Args:
        text: Source lyrics; blank lines mark stanzas.
        source: Source language code.
        target: Target language code.
        key: Groq API key.
        operation: Receives progress and checks for cancellation.

    Returns:
        The translation, with line N matching source line N.
    """
    lines = text.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    content = [line.strip() for line in lines if line.strip()]
    operation.report("Translating with Groq (online)…")
    translated = iter(request_lines(content, source, target, key, operation))
    return "\n".join(next(translated) if line.strip() else "" for line in lines)


def request_lines(lines, source, target, key, operation) -> list[str]:
    """Ask Groq again after broken JSON or a wrong number of lines."""
    model = os.environ.get("GROQ_MODEL", DEFAULT_MODEL)
    body = request_body(build_prompt(lines, source, target), model)
    for _ in range(ATTEMPTS):
        operation.check()
        try:
            result = parse_lines(post(body, key))
        except BadReply:
            continue
        if len(result) == len(lines):
            return result
    raise config.AppError(
        "Groq could not return the song line by line. Try again."
    )


def build_prompt(lines, source, target) -> str:
    """Describe the subtitle task and pass the lines as a JSON array."""
    return (
        f"Translate these song lyrics from {config.LANGUAGES[source]} to "
        f"{config.LANGUAGES[target]} for video subtitles. Translate the "
        "meaning naturally, including slang and idioms, not word for word. "
        f'Answer in JSON as {{"lines": [...]}} with exactly {len(lines)} '
        "strings: one translation per input line, in the same order. Never "
        "merge, split, skip, or explain lines.\n\n"
        + json.dumps(lines, ensure_ascii=False)
    )


def request_body(prompt: str, model: str) -> dict:
    """Request a JSON object holding the translated lines."""
    return {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "response_format": response_format(model),
    }


def response_format(model: str) -> dict:
    """Use a strict schema where Groq supports it, else plain JSON mode."""
    if not model.startswith(STRICT_SCHEMA_MODELS):
        return {"type": "json_object"}
    return {
        "type": "json_schema",
        "json_schema": {"name": "lyrics", "strict": True, "schema": SCHEMA},
    }


def post(body: dict, key: str) -> dict:
    """Send one request, turning network failures into readable errors."""
    request = urllib.request.Request(
        API_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "User-Agent": "SongWords",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as reply:
            return json.loads(reply.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        raise http_error(error) from error
    except (urllib.error.URLError, TimeoutError) as error:
        raise config.AppError(
            "Groq could not be reached. Check the internet connection."
        ) from error


def http_error(error: urllib.error.HTTPError) -> config.AppError:
    """Mark Groq's rejected JSON generations as worth another attempt."""
    try:
        details = error.read().decode("utf-8", "replace")
    except (AttributeError, OSError):
        details = ""
    if error.code == 400 and "json_validate_failed" in details:
        return BadReply("Groq returned an unreadable answer.")
    return config.AppError(http_message(error.code))


def http_message(status: int) -> str:
    """Explain the HTTP failures a user can act on."""
    if status == 429:
        return "Groq's free limit was reached. Wait a minute and try again."
    if status in (401, 403):
        return f"Groq rejected the key. Check {KEY_FILE}."
    if status == 404:
        return "This Groq model is not available. Check GROQ_MODEL."
    if status == 400:
        return "Groq rejected the request. Try another GROQ_MODEL."
    return f"Groq failed with HTTP error {status}. Try again later."


def parse_lines(response: dict) -> list[str]:
    """Extract the translated lines, explaining empty or refused answers."""
    choices = response.get("choices") or []
    text = choices[0].get("message", {}).get("content") if choices else None
    if not text:
        raise BadReply("Groq returned no translation. Try again.")
    try:
        lines = json.loads(text).get("lines")
    except (json.JSONDecodeError, AttributeError) as error:
        raise BadReply("Groq returned an unreadable answer.") from error
    if not isinstance(lines, list):
        raise BadReply("Groq returned an unreadable answer.")
    return [" ".join(str(line).split()) for line in lines]
