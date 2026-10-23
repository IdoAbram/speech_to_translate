"""CTranslate2 inference for one installed language pair."""

import contextlib
import gc
import pathlib

from speech_translate import config, i18n

OUTPUT_LIMIT = 768


class DecodeLimit(config.AppError):
    """The decoder exhausted its output budget and needs a smaller passage."""


@contextlib.contextmanager
def open_engine(path: pathlib.Path):
    """Keep only the current translation model resident in CPU memory."""
    import ctranslate2

    engine = ctranslate2.Translator(
        str(path / "model"),
        device="cpu",
        compute_type="int8",
        inter_threads=1,
        intra_threads=config.THREADS,
    )
    try:
        yield engine
    finally:
        engine.unload_model()
        del engine
        gc.collect()


def translate_tokens(engine, tokenizer, tokens: list, prefix: str) -> str:
    """Decode one bounded input, rejecting truncated or empty output."""
    result = engine.translate_batch(
        [tokenizer.prepare(tokens)],
        target_prefix=[[prefix]] if prefix else None,
        beam_size=4,
        length_penalty=1.0,
        repetition_penalty=1.05,
        max_input_length=0,
        max_decoding_length=OUTPUT_LIMIT,
    )[0]
    translated = result.hypotheses[0]
    if len(translated) >= OUTPUT_LIMIT:
        raise DecodeLimit(i18n.tr("The decoder needs a smaller passage."))
    if prefix and translated and translated[0] == prefix:
        translated = translated[1:]
    return decode_output(tokenizer, translated)


def decode_output(tokenizer, translated) -> str:
    """Normalize output spacing and reject empty model predictions."""
    text = tokenizer.decode(translated).replace("▁", " ").strip()
    if not text:
        raise config.AppError(
            i18n.tr("A line could not be translated. Try editing it.")
        )
    return " ".join(text.split())
