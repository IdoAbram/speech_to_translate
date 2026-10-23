"""Streaming downloads and atomic metadata writes used during setup only."""

import json
import pathlib
import urllib.request


def read_json(path: pathlib.Path) -> dict:
    """Read existing metadata or return an empty manifest."""
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def write_json(path: pathlib.Path, data: dict) -> None:
    """Replace metadata only after its complete contents have been written."""
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(data, indent=2), encoding="utf-8")
    temporary.replace(path)


def fetch_json(url: str) -> dict:
    """Read a model repository description with a finite connection timeout."""
    with urllib.request.urlopen(url, timeout=60) as response:
        return json.load(response)


def download(url: str, destination: pathlib.Path) -> None:
    """Keep incomplete downloads separate from installed model files."""
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    request = urllib.request.Request(
        url, headers={"User-Agent": "SongSetup/1.0"}
    )
    with urllib.request.urlopen(request, timeout=120) as response:
        with partial.open("wb") as output:
            copy_response(response, output)
    partial.replace(destination)


def copy_response(response, output) -> None:
    """Stream a response and reject a truncated Content-Length transfer."""
    total = int(response.headers.get("Content-Length", 0))
    count = 0
    reported = -1
    while block := response.read(1024 * 1024):
        output.write(block)
        count += len(block)
        bucket = count // (25 * 1024 * 1024)
        if bucket != reported:
            print(f"Downloaded {count / 1024**2:.0f} MB", flush=True)
            reported = bucket
    if total and count != total:
        raise OSError("Incomplete download. Run setup again.")
