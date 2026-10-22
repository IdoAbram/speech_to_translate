"""Independent command-line access to speech and translation stages."""

import argparse
import pathlib
import sys

from speech_translate import config, speech, translation


def build_parser() -> argparse.ArgumentParser:
    """Create the two CLI subcommands with explicit language selections."""
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    add_speech_arguments(commands.add_parser("transcribe"))
    add_translation_arguments(commands.add_parser("translate"))
    return parser


def add_speech_arguments(parser: argparse.ArgumentParser) -> None:
    """Describe the audio input and selected speech model."""
    parser.add_argument("audio", type=pathlib.Path)
    parser.add_argument("--language", choices=config.LANGUAGES, default=None)
    parser.add_argument(
        "--model", choices=config.SPEECH_MODELS, default="small"
    )
    parser.add_argument("--output", type=pathlib.Path, required=True)


def add_translation_arguments(parser: argparse.ArgumentParser) -> None:
    """Describe the text input and source/target languages."""
    parser.add_argument("text", type=pathlib.Path)
    parser.add_argument("--source", choices=config.LANGUAGES, required=True)
    parser.add_argument("--target", choices=config.LANGUAGES, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)


def validate_output(args, parser: argparse.ArgumentParser) -> None:
    """Avoid overwriting an input file or an existing result."""
    source = args.audio if args.command == "transcribe" else args.text
    if source.resolve() == args.output.resolve() or args.output.exists():
        parser.error("Choose a new output filename to preserve existing files.")


def execute(args) -> str:
    """Run the selected stage and return its formatted text."""
    if args.command == "transcribe":
        return speech.transcribe(args.audio, args.language, args.model).text
    text = args.text.read_text(encoding="utf-8-sig")
    return translation.translate(text, args.source, args.target)


def main(argv=None) -> int:
    """Process a local file and save Unicode output without overwriting."""
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_output(args, parser)
    config.offline_mode()
    try:
        text = execute(args)
        with args.output.open("x", encoding="utf-8-sig") as output:
            output.write(text)
    except (config.AppError, OSError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
    print(f"Saved {args.output}")
    return 0
