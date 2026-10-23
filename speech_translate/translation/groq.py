"""Online lyric translation with the free Groq API.

The song is sent in parts of a few verses, so the model sees enough context
for slang while each answer stays short enough to come back complete. A JSON
answer holds one translation per non-empty source line; the app checks the
count, which keeps subtitles aligned. Free-plan rate limits are waited out.
"""

import itertools
import json
import os
import pathlib
import time
import urllib.error
import urllib.request

from speech_translate import config, i18n

KEY_FILE = "groq_key.txt"
DEFAULT_MODEL = "openai/gpt-oss-120b"
API_URL = "https://api.groq.com/openai/v1/chat/completions"
TIMEOUT_SECONDS = 120
ATTEMPTS = 3
# Long songs in one request came back with dropped lines or broken JSON.
PART_LINES = 15
# Free-plan token limits reset within a minute; longer waits mean a daily cap.
MAX_WAIT_SECONDS = 60
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


class RateLimited(config.AppError):
    """The free plan's short-term limit was reached; retry after a pause."""

    def __init__(self, message: str, seconds: float):
        super().__init__(message)
        self.seconds = seconds


def api_key(root=config.ROOT) -> str:
    """Return the Groq key from the environment or a saved key file.

    Args:
        root: Folder that may contain a key file next to the app.

    Returns:
        The key, or an empty string when Groq is not configured.
    """
    key = os.environ.get("GROQ_API_KEY", "").strip()
    for path in (user_key_path(), root / KEY_FILE):
        if not key and path.is_file():
            key = path.read_text(encoding="utf-8-sig").strip()
    return key


def user_key_path() -> pathlib.Path:
    """Locate the key saved from the app for the current Windows user."""
    return config.settings_dir() / KEY_FILE


def save_key(key: str) -> None:
    """Store a pasted key for this Windows user, replacing an earlier one."""
    key = key.strip()
    if not key or any(character.isspace() for character in key):
        raise config.AppError(
            i18n.tr("Paste the whole Groq key, without spaces.")
        )
    path = user_key_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(key, encoding="utf-8")


def remove_key() -> None:
    """Forget the key saved from the app; other key sources are kept."""
    user_key_path().unlink(missing_ok=True)


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
    translated = iter(translate_parts(content, source, target, key, operation))
    return "\n".join(next(translated) if line.strip() else "" for line in lines)


def translate_parts(lines, source, target, key, operation) -> list[str]:
    """Translate a few verses per request and report progress per part."""
    parts = list(itertools.batched(lines, PART_LINES))
    translated = []
    for index, part in enumerate(parts):
        operation.report(
            i18n.tr(
                "Translating with Groq: part {part} of {total}…",
                part=index + 1,
                total=len(parts),
            ),
            int(100 * index / len(parts)),
        )
        translated += request_lines(list(part), source, target, key, operation)
    return translated


def request_lines(lines, source, target, key, operation) -> list[str]:
    """Ask Groq again after broken JSON, a wrong count, or a rate limit."""
    model = os.environ.get("GROQ_MODEL", DEFAULT_MODEL)
    body = request_body(build_prompt(lines, source, target), model)
    failure = i18n.tr("Groq could not return the song line by line. Try again.")
    for _ in range(ATTEMPTS):
        operation.check()
        try:
            result = parse_lines(post(body, key))
        except BadReply:
            continue
        except RateLimited as error:
            failure = str(error)
            wait_for_limit(error.seconds, operation)
            continue
        if len(result) == len(lines):
            return result
    raise config.AppError(failure)


def wait_for_limit(seconds: float, operation) -> None:
    """Pause for the free plan's reset, staying responsive to Cancel."""
    if seconds > MAX_WAIT_SECONDS:
        raise config.AppError(
            i18n.tr("Groq's free daily limit was reached. Try again later.")
        )
    deadline = time.monotonic() + seconds
    while (left := deadline - time.monotonic()) > 0:
        seconds = int(left) + 1
        operation.report(
            i18n.tr("Groq free limit: waiting {seconds} s…", seconds=seconds)
        )
        time.sleep(min(1.0, left))


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
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.2,
        "response_format": response_format(model),
    }
    if model.startswith("openai/gpt-oss"):
        # Translation needs little reasoning; this saves free-plan tokens.
        body["reasoning_effort"] = "low"
    return body


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
            i18n.tr("Groq could not be reached. Check the internet connection.")
        ) from error


def http_error(error: urllib.error.HTTPError) -> config.AppError:
    """Mark broken JSON and short rate limits as worth another attempt."""
    try:
        details = error.read().decode("utf-8", "replace")
    except (AttributeError, OSError):
        details = ""
    if error.code == 400 and "json_validate_failed" in details:
        return BadReply(i18n.tr("Groq returned an unreadable answer."))
    if error.code == 429:
        return RateLimited(http_message(429), retry_after(error.headers))
    return config.AppError(http_message(error.code))


def retry_after(headers) -> float:
    """Read Groq's suggested pause, assuming a short one if it is absent."""
    try:
        return float((headers or {}).get("retry-after", 10))
    except ValueError:
        return 10.0


def http_message(status: int) -> str:
    """Explain the HTTP failures a user can act on."""
    if status == 429:
        return i18n.tr(
            "Groq's free limit was reached. Wait a minute and try again."
        )
    if status in (401, 403):
        return i18n.tr(
            "Groq rejected the key. Check it under Online translation."
        )
    if status == 404:
        return i18n.tr("This Groq model is not available. Check GROQ_MODEL.")
    if status == 400:
        return i18n.tr("Groq rejected the request. Try another GROQ_MODEL.")
    return i18n.tr(
        "Groq failed with HTTP error {status}. Try again later.",
        status=status,
    )


def parse_lines(response: dict) -> list[str]:
    """Extract the translated lines, explaining empty or refused answers."""
    choices = response.get("choices") or []
    text = choices[0].get("message", {}).get("content") if choices else None
    if not text:
        raise BadReply(i18n.tr("Groq returned no translation. Try again."))
    try:
        lines = json.loads(text).get("lines")
    except (json.JSONDecodeError, AttributeError) as error:
        raise BadReply(
            i18n.tr("Groq returned an unreadable answer.")
        ) from error
    if not isinstance(lines, list):
        raise BadReply(i18n.tr("Groq returned an unreadable answer."))
    return [" ".join(str(line).split()) for line in lines]
