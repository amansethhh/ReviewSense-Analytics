"""
Translation client with circuit breaker + timeout wrapper.

CRITICAL FIX: Added circuit breaker that detects ModuleNotFoundError on the
first call and permanently marks deep_translator as unavailable. This prevents
the 12–24s per-review hang caused by 3 retries × 4s timeout when the package
is not installed. The circuit re-tests on server restart.

Architecture:
  - Attempt 1: GoogleTranslator with 3s timeout
  - Retry 2-3: Only on network errors, NOT on import errors
  - Circuit breaker: ModuleNotFoundError → fail immediately on all future calls
"""

import time
import logging
import threading
from concurrent.futures import (
    ThreadPoolExecutor,
    TimeoutError as FuturesTimeoutError,
)
from typing import Tuple

logger = logging.getLogger("reviewsense.translation_client")

MAX_RETRIES = 3
BASE_DELAY_S = 0.3         # 0.3s → 0.6s → 1.2s (reduced from 0.5s)
_GOOGLE_TIMEOUT_S = 3.0    # reduced from 4.0s — fail faster per attempt

# ── Circuit breaker state ─────────────────────────────────────────────────────
# _package_available: None = untested, True = OK, False = broken
_circuit_lock = threading.Lock()
_package_available: bool | None = None


def _check_package_availability() -> bool:
    """Test if deep_translator is importable. Cached after first check."""
    global _package_available
    with _circuit_lock:
        if _package_available is not None:
            return _package_available
        try:
            import importlib
            importlib.import_module("deep_translator")
            _package_available = True
            logger.info("[CIRCUIT] deep_translator package: AVAILABLE")
        except ImportError:
            _package_available = False
            logger.error(
                "[CIRCUIT] deep_translator package NOT INSTALLED. "
                "All translations will use original text. "
                "Run: pip install deep-translator==1.11.4"
            )
        return _package_available


# ── Dedicated executor ────────────────────────────────────────────────────────
_google_executor = ThreadPoolExecutor(
    max_workers=3,
    thread_name_prefix="google_translate",
)


def _google_translate_with_timeout(
    text: str,
    source: str,
    target: str,
    timeout: float = _GOOGLE_TIMEOUT_S,
) -> str:
    """
    Run GoogleTranslator.translate() in a thread with a hard wall-clock timeout.
    Raises TimeoutError if the call exceeds `timeout` seconds.
    Raises ImportError if deep_translator is not installed (circuit break).
    """
    # C4: deferred import — but check circuit first
    if not _check_package_availability():
        raise ImportError("deep_translator is not installed — circuit open")

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

    CRITICAL FIX: ImportError (missing package) triggers circuit breaker
    and fails immediately — no retries, no 12s hang.

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

        except ImportError as e:
            # CIRCUIT BREAKER: package not installed — fail immediately
            # Do NOT retry, do NOT wait — would be 12s of wasted time
            logger.error(
                "[CIRCUIT] Aborting translation — package unavailable: %s", e
            )
            return (text, "failed")

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
