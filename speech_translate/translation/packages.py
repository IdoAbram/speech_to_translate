"""Language routing and validation of local translation packages."""

import pathlib

from speech_translate import config, i18n

# NLLB-200 names languages with FLORES-200 codes instead of ISO codes.
LANGUAGE_TOKENS = {"en": "eng_Latn", "he": "heb_Hebr", "pl": "pol_Latn"}


def route(source: str, target: str) -> list[tuple[str, str]]:
    """Translate every supported pair directly with the multilingual model."""
    config.validate_language(source)
    config.validate_language(target)
    if source == target:
        return []
    return [(source, target)]


def language_token(code: str) -> str:
    """Return the offline model's marker for a supported language code."""
    config.validate_language(code)
    return LANGUAGE_TOKENS[code]


def multilingual_path(models_dir) -> pathlib.Path:
    """Require complete local multilingual assets without network access."""
    path = pathlib.Path(models_dir) / "translation" / "nllb"
    required = (
        "model/model.bin",
        "model/config.json",
        "model/shared_vocabulary.json",
        "sentencepiece.bpe.model",
    )
    if not all((path / name).is_file() for name in required):
        raise config.AppError(
            i18n.tr(
                "The upgraded translation model is missing. Run "
                "setup_models.py on a connected computer, or copy the "
                "complete models folder."
            )
        )
    return path
