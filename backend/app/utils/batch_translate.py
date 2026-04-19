"""
Batch translation module for bulk pipeline optimization.

Groups reviews by detected language → translates all reviews of the
same language in batched API calls → avoids N separate HTTP requests.

Thread-safe. Uses deep-translator GoogleTranslator with retry logic.
Falls back to Helsinki-NLP for individual failures.
"""

import re
import time
import logging
import threading
from collections import defaultdict
from typing import Optional
from concurrent.futures import (
    ThreadPoolExecutor,
    TimeoutError as FuturesTimeoutError,
)

logger = logging.getLogger("reviewsense.batch_translate")

# Language code mapping for deep-translator (Google API format)
LANGUAGE_SOURCE_MAP = {
    'hi': 'hi', 'es': 'es', 'fr': 'fr', 'de': 'de',
    'zh-cn': 'zh-CN', 'zh': 'zh-CN', 'ko': 'ko',
    'pt': 'pt', 'it': 'it', 'ar': 'ar', 'ru': 'ru',
    'ja': 'ja', 'pl': 'pl', 'nl': 'nl', 'tr': 'tr',
    'sv': 'sv', 'th': 'th', 'bn': 'bn', 'ta': 'ta',
}

SUFFIX_PATTERN = re.compile(
    r'\s*[,.]?\s*(?:Hindi|Chinese|Korean|Arabic|Russian|German|French|'
    r'Spanish|Italian|Portuguese|Polish|Japanese|Thai|Turkish|Swedish|'
    r'Dutch|Bengali|Tamil)\s*[.]?\s*$',
    re.IGNORECASE,
)

BATCH_SIZE = 30         # Max reviews per concatenated request
BATCH_DELIMITER = ' ||| '
MAX_RETRIES = 3
_GOOGLE_TIMEOUT_S = 8.0  # per-batch timeout

# Dedicated executor for batch translation
_batch_executor = ThreadPoolExecutor(
    max_workers=2,
    thread_name_prefix="batch_translate",
)


def _clean_translation(text: str) -> str:
    """Strip appended language-name suffixes from translations."""
    if not text:
        return text
    return SUFFIX_PATTERN.sub('', text).strip()


def _google_translate_batch(
    joined_text: str,
    source_code: str,
    timeout: float = _GOOGLE_TIMEOUT_S,
) -> Optional[str]:
    """Translate concatenated text via Google with timeout."""
    try:
        from deep_translator import GoogleTranslator

        future = _batch_executor.submit(
            lambda: GoogleTranslator(
                source=source_code, target='en'
            ).translate(joined_text)
        )
        result = future.result(timeout=timeout)
        return result
    except FuturesTimeoutError:
        logger.warning(
            "Batch Google translate exceeded %ss timeout", timeout
        )
        return None
    except Exception as e:
        logger.warning("Batch Google translate failed: %s", e)
        return None


def _translate_individually_helsinki(
    texts: list[str],
    source_lang: str,
) -> list[str]:
    """Fallback: translate one-by-one using Helsinki-NLP."""
    results = []
    try:
        from src.translator import detect_and_translate
        for text in texts:
            try:
                lang_result = detect_and_translate(text)
                if isinstance(lang_result, dict):
                    translated = lang_result.get("translated_text", text)
                    results.append(_clean_translation(translated))
                else:
                    results.append(text)
            except Exception:
                results.append(text)
    except ImportError:
        results = list(texts)
    return results


def _translate_individually_google(
    texts: list[str],
    source_code: str,
) -> list[str]:
    """Fallback: translate one-by-one using Google."""
    results = []
    try:
        from deep_translator import GoogleTranslator
        for text in texts:
            try:
                t = GoogleTranslator(
                    source=source_code, target='en'
                ).translate(text)
                results.append(_clean_translation(t) if t else text)
            except Exception:
                results.append(text)
    except ImportError:
        results = list(texts)
    return results


def translate_batch_for_lang(
    texts: list[str],
    source_lang: str,
) -> list[str]:
    """
    Translate a list of texts from source_lang to English in batches.
    Uses concatenated batching with delimiter splitting.
    Falls back to individual translation on split mismatch.
    """
    source_code = LANGUAGE_SOURCE_MAP.get(source_lang, 'auto')
    results: list[str] = []

    for batch_start in range(0, len(texts), BATCH_SIZE):
        batch = texts[batch_start:batch_start + BATCH_SIZE]
        translated_batch = None

        for attempt in range(MAX_RETRIES):
            joined = BATCH_DELIMITER.join(batch)

            raw_translated = _google_translate_batch(
                joined, source_code
            )

            if raw_translated is None:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(0.5 * (attempt + 1))
                continue

            parts = raw_translated.split(BATCH_DELIMITER)

            if len(parts) == len(batch):
                translated_batch = [
                    _clean_translation(p.strip()) for p in parts
                ]
                break
            else:
                logger.warning(
                    "[BATCH] Split mismatch (%d vs %d) for %s, "
                    "attempt %d — retrying",
                    len(parts), len(batch), source_lang, attempt + 1,
                )
                if attempt < MAX_RETRIES - 1:
                    time.sleep(0.5 * (attempt + 1))

        # All batch attempts failed — fall back to individual
        if translated_batch is None:
            logger.warning(
                "[BATCH] All batch attempts failed for %s, "
                "falling back to individual translation",
                source_lang,
            )
            translated_batch = _translate_individually_helsinki(
                batch, source_lang
            )

        results.extend(translated_batch)

    return results


def batch_translate_reviews(
    reviews: list[str],
    detected_languages: list[str],
) -> list[str]:
    """
    Main entry point. Translates reviews grouped by language.
    Returns translated English versions in the SAME ORDER as input.
    English reviews are returned unchanged.
    """
    # Build index map: lang → [(original_index, text)]
    lang_groups: dict[str, list[tuple[int, str]]] = defaultdict(list)
    for idx, (review, lang) in enumerate(
        zip(reviews, detected_languages)
    ):
        lang_groups[lang].append((idx, review))

    # Allocate output array
    translated = [''] * len(reviews)
    stats = {"english_skipped": 0, "batch_translated": 0}

    for lang, indexed_texts in lang_groups.items():
        indices = [i for i, _ in indexed_texts]
        texts = [t for _, t in indexed_texts]

        if lang == 'en':
            # No translation needed
            for idx, text in zip(indices, texts):
                translated[idx] = text
            stats["english_skipped"] += len(texts)
        else:
            batch_results = translate_batch_for_lang(texts, lang)
            for idx, result in zip(indices, batch_results):
                translated[idx] = result
            stats["batch_translated"] += len(texts)

    logger.info(
        "[BATCH] Translation complete: %d English (skipped), "
        "%d batch-translated",
        stats["english_skipped"],
        stats["batch_translated"],
    )

    return translated
