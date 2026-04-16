"""
Phase 2, Part 1: LRU Prediction Cache.

Thread-safe OrderedDict-based LRU cache for ML prediction
results. SHA-256 key generation with canonical JSON
serialization.

INVARIANT:
  All cache keys are SHA-256(english_text | model | options_json).
  NEVER pass raw non-English text to get_cache_key().
  Translation must happen BEFORE any cache interaction.

CACHE RULES (enforced by callers, documented here):
  - Cache only COMPLETED predictions (status: success)
  - Strip lime_features before storing (C9)
  - NEVER cache if include_lime=True was in request
  - NEVER cache error responses or partial results
  - Cache key includes: text, model, and ALL feature flags
    (include_absa, include_sarcasm, include_lime)
  - include_lime MUST be part of the key so that a non-LIME
    cached result is never returned for a LIME request

No external dependencies — uses collections.OrderedDict,
hashlib, json, threading from stdlib.
"""

import json
import hashlib
import threading
import logging
from collections import OrderedDict
from typing import Any

logger = logging.getLogger("reviewsense.cache")


class PredictionCache:
    """
    Thread-safe LRU cache backed by OrderedDict.

    maxsize=512 entries. On capacity overflow, the least
    recently used entry is evicted before inserting.

    All read/write operations are guarded by threading.Lock.
    """

    def __init__(self, maxsize: int = 512) -> None:
        self._store: OrderedDict[str, dict] = OrderedDict()
        self._maxsize: int = maxsize
        self._lock: threading.Lock = threading.Lock()
        self._hits: int = 0
        self._misses: int = 0
        logger.info(
            f"PredictionCache initialized "
            f"(maxsize={maxsize})"
        )

    @staticmethod
    def get_cache_key(
        text: str,
        model: str,
        options: dict[str, Any],
    ) -> str:
        """
        Generate a cache key from text + model + options.

        INVARIANT: `text` MUST be English (post-translation).
        Callers are responsible for translating before calling.

        The key includes ALL feature flags (include_absa,
        include_sarcasm, include_lime) to prevent cross-
        contamination between requests with different flags.

        Canonical JSON-serializes options (sorted keys),
        then SHA-256 hashes the full string. Returns first
        32 hex chars (128-bit — sufficient for collision
        avoidance at 512 entries).
        """
        options_json = json.dumps(
            options, sort_keys=True, default=str
        )
        raw = f"{text.strip().lower()}|{model}|{options_json}"
        return hashlib.sha256(
            raw.encode("utf-8")
        ).hexdigest()[:32]

    def get(self, key: str) -> dict | None:
        """
        Retrieve a cached prediction result.

        Returns None on cache miss. On hit, moves the
        entry to the end (most recently used).
        """
        with self._lock:
            if key in self._store:
                # Move to end = most recently used
                self._store.move_to_end(key)
                self._hits += 1
                return self._store[key]
            self._misses += 1
            return None

    def set(self, key: str, value: dict) -> None:
        """
        Store a prediction result in the cache.

        If key already exists, update and move to end.
        If at capacity, evict the LRU entry (first item)
        before inserting.
        """
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
                self._store[key] = value
            else:
                if len(self._store) >= self._maxsize:
                    # Evict LRU (first item)
                    evicted_key, _ = (
                        self._store.popitem(last=False)
                    )
                    logger.debug(
                        f"Cache evicted LRU: "
                        f"{evicted_key[:8]}..."
                    )
                self._store[key] = value

    def invalidate(self, key: str) -> None:
        """Remove a specific entry from the cache."""
        with self._lock:
            self._store.pop(key, None)

    def clear(self) -> None:
        """Clear all entries and reset counters."""
        with self._lock:
            self._store.clear()
            self._hits = 0
            self._misses = 0
            logger.info("PredictionCache cleared")

    def stats(self) -> dict[str, Any]:
        """
        Return cache statistics.

        Returns:
            hits, misses, size, capacity, hit_rate
        """
        with self._lock:
            total = self._hits + self._misses
            return {
                "hits": self._hits,
                "misses": self._misses,
                "size": len(self._store),
                "capacity": self._maxsize,
                "hit_rate": (
                    round(self._hits / total, 4)
                    if total > 0
                    else 0.0
                ),
            }


# ── Module-level singleton ─────────────────────────────────
# INVARIANT: All keys are SHA-256(english_text|model|options).
# NEVER pass raw non-English text to get() or set().
# Translation must happen BEFORE any cache interaction.
prediction_cache = PredictionCache(maxsize=512)
