"""Line-aligned translation in all six supported language directions."""

from speech_translate import config
from speech_translate.translation import (
    engine,
    groq,
    packages,
    passages,
    tokenizers,
)


def translate(
    text: str,
    source: str,
    target: str,
    *,
    models_dir=config.MODELS,
    progress=config.ignore_progress,
    cancel=None,
    notice=config.ignore_notice,
) -> str:
    """Translate any length of text, keeping the source line layout."""
    steps = packages.route(source, target)
    if not text.strip():
        raise config.AppError("Transcribe a song or enter some text first.")
    operation = config.Operation(progress, cancel, notice)
    operation.check()
    if steps:
        text = choose_translator(text, source, target, models_dir, operation)
    operation.report("Translation ready.", 100)
    return text


def choose_translator(text, source, target, models_dir, operation) -> str:
    """Prefer Groq when a key is configured, falling back to offline."""
    key = groq.api_key()
    if not key:
        return translate_document(text, source, target, models_dir, operation)
    try:
        return groq.translate_lyrics(text, source, target, key, operation)
    except config.Cancelled:
        raise
    except (config.AppError, OSError, ValueError) as error:
        operation.notice(
            f"Groq was unavailable ({error}) Used the offline model, "
            "which translates more literally."
        )
        operation.report("Groq unavailable. Using the offline model…")
        return translate_document(text, source, target, models_dir, operation)


def translate_document(text, source, target, models_dir, operation) -> str:
    """Load one direct multilingual model for the entire document."""
    config.offline_mode()
    path = packages.multilingual_path(models_dir)
    operation.report("Loading the translation model…")
    tokenizer = tokenizers.MultilingualTokenizer(path, source)
    lines = passages.prepare(text, tokenizer)
    with engine.open_engine(path) as model:
        translator = passages.PassageTranslator(
            model, tokenizer, f"__{target}__", operation
        )
        return translate_lines(lines, translator, operation)


def translate_lines(lines, translator, operation) -> str:
    """Translate line by line so line N of the output matches line N.

    Args:
        lines: Token chunks per source line; empty for blank lines.
        translator: Decodes chunks and reuses repeated lines.
        operation: Receives progress and checks for cancellation.

    Returns:
        The translation with exactly the source's line and stanza layout.
    """
    total, completed, output = max(sum(map(len, lines)), 1), 0, []
    operation.report(f"Translating passage 1 of {total}…", 0)
    for chunks in lines:
        output.append(" ".join(map(translator.translate, chunks)))
        completed += len(chunks)
        message = f"Translated {completed} of {total} passages…"
        operation.report(message, min(99, int(100 * completed / total)))
    return "\n".join(output)
