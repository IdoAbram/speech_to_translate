"""Contextual offline translation in all six supported language directions."""

from speech_translate import config
from speech_translate.translation import engine, packages, passages, tokenizers


def translate(
    text: str,
    source: str,
    target: str,
    *,
    models_dir=config.MODELS,
    progress=config.ignore_progress,
    cancel=None,
) -> str:
    """Translate any length of text in bounded, connected passages."""
    steps = packages.route(source, target)
    if not text.strip():
        raise config.AppError("Transcribe a song or enter some text first.")
    operation = config.Operation(progress, cancel)
    operation.check()
    if steps:
        text = translate_document(text, source, target, models_dir, operation)
    operation.report("Translation ready.", 100)
    return text


def translate_document(text, source, target, models_dir, operation) -> str:
    """Load one direct multilingual model for the entire document."""
    config.offline_mode()
    path = packages.multilingual_path(models_dir)
    operation.report("Loading the translation model…")
    tokenizer = tokenizers.MultilingualTokenizer(path, source)
    stanzas = passages.prepare(text, tokenizer)
    with engine.open_engine(path) as model:
        return translate_stanzas(
            stanzas, model, tokenizer, f"__{target}__", operation, "\n" in text
        )


def translate_stanzas(stanzas, model, tokenizer, prefix, operation, lyrics):
    """Keep repeated choruses and stanza gaps, reporting completed passages."""
    total = max(sum(len(chunks) for chunks in stanzas), 1)
    completed, output = 0, []
    translator = passages.PassageTranslator(model, tokenizer, prefix, operation)
    operation.report(f"Translating passage 1 of {total}…", 0)
    for chunks in stanzas:
        translated = []
        for tokens in chunks:
            translated.append(translator.translate(tokens))
            completed += 1
            operation.report(
                f"Translated {completed} of {total} passages…",
                min(99, int(100 * completed / total)),
            )
        output.append(passages.format_stanza(" ".join(translated), lyrics))
    return "\n\n".join(output)
