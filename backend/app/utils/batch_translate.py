"""
Batch translation module — NLLB-only (V4 architecture).

V4: All translations use NLLB locally.
Groups reviews by language → translates via NLLB.
No external APIs, no Helsinki fallback, no Google.

Translation is for DISPLAY ONLY — never affects sentiment.
"""

import logging
from collections import defaultdict

logger = logging.getLogger("reviewsense.batch_translate")


def translate_batch_for_lang(
    texts: list[str],
    source_lang: str,
) -> list[str]:
    """
    Translate a list of texts from source_lang to English via NLLB.

    If translation fails for any text, returns original text.
    """
    from src.models.translation import translate_to_english

    results = []
    for text in texts:
        translated, method = translate_to_english(text, source_lang)
        results.append(translated)

    logger.info(
        "[NLLB-BATCH] Translated %d texts from %s",
        len(texts), source_lang,
    )
    return results


def batch_translate_reviews(
    reviews: list[str],
    detected_languages: list[str],
) -> list[str]:
    """
    Main entry point. Translates reviews grouped by language
    using NLLB. Returns translated English versions in the
    SAME ORDER as input. English reviews returned unchanged.
    """
    # Build index map: lang → [(original_index, text)]
    lang_groups: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for idx, (review, lang) in enumerate(
        zip(reviews, detected_languages)
    ):
        lang_groups[lang].append((idx, review))

    # Allocate output array
    translated = [''] * len(reviews)
    stats = {"english_skipped": 0, "nllb_translated": 0}

    for lang, indexed_texts in lang_groups.items():
        indices = [i for i, _ in indexed_texts]
        texts = [t for _, t in indexed_texts]

        if lang == 'en':
            for idx, text in zip(indices, texts):
                translated[idx] = text
            stats["english_skipped"] += len(texts)
        else:
            batch_results = translate_batch_for_lang(texts, lang)
            for idx, result in zip(indices, batch_results):
                translated[idx] = result
            stats["nllb_translated"] += len(texts)

    logger.info(
        "[NLLB-BATCH] Complete: %d English (skipped), "
        "%d NLLB-translated",
        stats["english_skipped"],
        stats["nllb_translated"],
    )

    return translated
