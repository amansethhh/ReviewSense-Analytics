"""
W4-4 / Phase-6: Translation client with timeout wrapper and
exponential backoff retry logic.

Wraps deep-translator's GoogleTranslator with:
  - Per-attempt 4s timeout via ThreadPoolExecutor future
  - 3 retry attempts with exponential backoff (0.5s, 1.0s, 2.0s)
  - Detailed per-attempt logging (no silent failures)

Import is deferred to function body per constraint C4 to prevent
import errors on servers where the package is not installed.

NOTE: GoogleTranslator (deep-translator) is used as Tier 2.
In environments without outbound HTTP to translate.googleapis.com,
this tier will always fail and the system degrades to Tier 3
(raw prediction on untranslated text). This is intentional.
To test Google reachability: python backend/tests/test_google_translate_live.py
"""

import time
import logging
from concurrent.futures import (
    ThreadPoolExecutor,
    TimeoutError as FuturesTimeoutError,
)
from typing import Tuple

logger = logging.getLogger("reviewsense.translation_client")

MAX_RETRIES = 3
BASE_DELAY_S = 0.5        # 0.5s → 1.0s → 2.0s
_GOOGLE_TIMEOUT_S = 4.0   # per-attempt wall-clock cap

# Dedicated executor — kept alive for the process lifetime so we
# don't pay thread-creation cost on every call.
_google_executor = ThreadPoolExecutor(
    max_workers=2,
    thread_name_prefix="google_translate",
)


def _google_translate_with_timeout(
    text: str,
    source: str,
    target: str,
    timeout: float = _GOOGLE_TIMEOUT_S,
) -> str:
    """
    Run GoogleTranslator.translate() in a thread with a hard
    wall-clock timeout.  Raises TimeoutError if the call exceeds
    `timeout` seconds.

    Uses concurrent.futures so it works identically on Windows
    and Unix (no SIGALRM required).
    """
    # C4: deferred import
    from deep_translator import GoogleTranslator

    future = _google_executor.submit(
        lambda: GoogleTranslator(
            source=source, target=target
        ).translate(text)
    )
    try:
        return future.result(timeout=timeout)
    except FuturesTimeoutError:
        future.cancel()
        raise TimeoutError(
            f"Google translate exceeded {timeout}s timeout"
        )


def translate_with_retry(
    text: str,
    source_lang: str,
    target_lang: str = "en",
    timeout: float = _GOOGLE_TIMEOUT_S,
) -> Tuple[str, str]:
    """
    Translate text using GoogleTranslator with per-attempt timeout
    and exponential backoff retry.

    Args:
        text:        The text to translate.
        source_lang: Source language code (e.g. 'es', 'fr', 'auto').
        target_lang: Target language code (default 'en').
        timeout:     Per-attempt wall-clock cap in seconds.

    Returns:
        Tuple of (translated_text, status) where status is
        'success' or 'failed'.
    """
    last_error: Exception | None = None

    for attempt in range(MAX_RETRIES):
        try:
            result = _google_translate_with_timeout(
                text, source_lang, target_lang, timeout
            )

            if result and result.strip():
                logger.debug(
                    "Google translation succeeded on attempt "
                    "%d/%d", attempt + 1, MAX_RETRIES
                )
                return (result.strip(), "success")

            # Empty result — treat as failure and retry
            last_error = ValueError("Empty translation result")
            logger.warning(
                "Google translate attempt %d/%d: empty result",
                attempt + 1, MAX_RETRIES,
            )

        except TimeoutError as e:
            last_error = e
            logger.warning(
                "Google translate attempt %d/%d: TimeoutError: %s",
                attempt + 1, MAX_RETRIES, e,
            )
        except Exception as e:
            last_error = e
            logger.warning(
                "Google translate attempt %d/%d: %s: %s",
                attempt + 1, MAX_RETRIES, type(e).__name__, e,
            )

        # Exponential backoff before next retry (skip after last)
        if attempt < MAX_RETRIES - 1:
            delay = BASE_DELAY_S * (2 ** attempt)
            logger.debug("Retrying in %.1fs…", delay)
            time.sleep(delay)

    # All retries exhausted
    logger.error(
        "Google translation failed after %d attempts. "
        "Last error: %s",
        MAX_RETRIES, last_error,
    )
    return (text, "failed")
