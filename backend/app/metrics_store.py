"""
Phase 2, Part 5: Lightweight in-memory metrics store.

Thread-safe request/latency/cache/timeout tracking with
rolling window for percentile computations.

No external dependencies — uses collections.deque +
threading.Lock from stdlib.
"""

import time
import threading
import logging
from collections import deque
from typing import Any

logger = logging.getLogger("reviewsense.metrics_store")


class MetricsStore:
    """
    Thread-safe in-memory metrics tracker.

    Tracks:
      - Total requests, cache hits/misses, inference timeouts
      - Rolling latency window (last 1000 requests) for
        percentile computation (p50/p95/p99)
      - Per-route request counts
      - Per-status-code error counts
      - Server uptime

    All mutations are guarded by threading.Lock().
    """

    def __init__(self, window_size: int = 1000) -> None:
        self._lock: threading.Lock = threading.Lock()
        self._start_time: float = time.monotonic()
        self._total_requests: int = 0
        self._cache_hits: int = 0
        self._cache_misses: int = 0
        self._inference_timeouts: int = 0
        self._latencies_ms: deque[float] = deque(
            maxlen=window_size
        )
        self._requests_by_route: dict[str, int] = {}
        self._errors_by_status: dict[int, int] = {}
        # W4-1: Translation metrics
        self._translation_counts: dict[str, int] = {
            "helsinki_success": 0,
            "google_success": 0,
            "failed": 0,
            "skipped_english": 0,
        }
        self._language_counts: dict[str, dict] = {}
        logger.info(
            f"MetricsStore initialized "
            f"(window={window_size})"
        )

    def record_request(
        self,
        path: str,
        latency_ms: float,
        status_code: int,
    ) -> None:
        """Record a completed HTTP request."""
        with self._lock:
            self._total_requests += 1
            self._latencies_ms.append(latency_ms)
            self._requests_by_route[path] = (
                self._requests_by_route.get(path, 0) + 1
            )
            if status_code >= 400:
                self._errors_by_status[status_code] = (
                    self._errors_by_status.get(
                        status_code, 0
                    ) + 1
                )

    def record_cache_hit(self) -> None:
        """Increment cache hit counter."""
        with self._lock:
            self._cache_hits += 1

    def record_cache_miss(self) -> None:
        """Increment cache miss counter."""
        with self._lock:
            self._cache_misses += 1

    def record_timeout(self) -> None:
        """Increment inference timeout counter."""
        with self._lock:
            self._inference_timeouts += 1

    def get_summary(self) -> dict[str, Any]:
        """
        Return a snapshot of all tracked metrics.

        Percentiles are computed from the rolling latency
        deque. If deque is empty, all latency fields = 0.0.
        """
        with self._lock:
            total_cache = (
                self._cache_hits + self._cache_misses
            )
            hit_rate = (
                round(self._cache_hits / total_cache, 2)
                if total_cache > 0
                else 0.0
            )

            if self._latencies_ms:
                sorted_lat = sorted(self._latencies_ms)
                n = len(sorted_lat)
                avg = round(sum(sorted_lat) / n, 2)
                p50 = round(
                    sorted_lat[int(n * 0.5)], 2
                )
                p95 = round(
                    sorted_lat[min(int(n * 0.95), n - 1)],
                    2,
                )
                p99 = round(
                    sorted_lat[min(int(n * 0.99), n - 1)],
                    2,
                )
            else:
                avg = p50 = p95 = p99 = 0.0

            uptime = round(
                time.monotonic() - self._start_time, 2
            )

            return {
                "total_requests": self._total_requests,
                "cache_hits": self._cache_hits,
                "cache_misses": self._cache_misses,
                "cache_hit_rate": hit_rate,
                "inference_timeouts": (
                    self._inference_timeouts
                ),
                "avg_latency_ms": avg,
                "p50_latency_ms": p50,
                "p95_latency_ms": p95,
                "p99_latency_ms": p99,
                "requests_by_route": dict(
                    self._requests_by_route
                ),
                "errors_by_status": dict(
                    self._errors_by_status
                ),
                "uptime_seconds": uptime,
            }

    def record_translation(
        self,
        method: str,
        language_code: str,
    ) -> None:
        """
        W4-1: Record a translation event.
        method: "helsinki" | "google" | "failed" | "skipped"

        Phase 8 / GAP 1: Persists to disk after every increment.
        """
        with self._lock:
            if method == "failed":
                key = "failed"
            elif method == "skipped":
                key = "skipped_english"
            else:
                key = f"{method}_success"
            self._translation_counts[key] = (
                self._translation_counts.get(key, 0) + 1
            )
            if language_code not in self._language_counts:
                self._language_counts[language_code] = {
                    "count": 0, "failed": 0,
                }
            self._language_counts[language_code][
                "count"] += 1
            if method == "failed":
                self._language_counts[language_code][
                    "failed"] += 1
            # GAP 1: Persist to disk after every update
            self._save_translation_stats()

    def get_translation_stats(self) -> dict:
        """W4-1: Return translation pipeline metrics."""
        with self._lock:
            total = sum(self._translation_counts.values())
            fail_count = self._translation_counts.get(
                "failed", 0)
            fail_rate = (
                round(fail_count / total * 100, 2)
                if total > 0 else 0.0
            )
            return {
                "total_translations": total,
                "method_breakdown": dict(
                    self._translation_counts),
                "failure_rate_pct": fail_rate,
                "per_language": {
                    k: dict(v) for k, v in
                    self._language_counts.items()
                },
            }

    def reset_translation_stats(self) -> None:
        """GAP 1: Reset all translation counters and clear disk file."""
        with self._lock:
            self._translation_counts = {
                "helsinki_success": 0,
                "google_success": 0,
                "failed": 0,
                "skipped_english": 0,
            }
            self._language_counts = {}
            self._save_translation_stats()

    # ── GAP 1: Translation stats persistence ───────────────
    def _save_translation_stats(self) -> None:
        """Persist translation stats to disk atomically.
        Called with self._lock already held."""
        import json
        try:
            data = {
                "translation_counts": dict(
                    self._translation_counts),
                "language_counts": {
                    k: dict(v) for k, v in
                    self._language_counts.items()
                },
            }
            _TRANSLATION_STATS_FILE.parent.mkdir(
                parents=True, exist_ok=True)
            tmp = _TRANSLATION_STATS_FILE.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            tmp.replace(_TRANSLATION_STATS_FILE)
        except IOError as e:
            logger.warning(
                "Could not save translation stats: %s", e)

    def _load_translation_stats(self) -> None:
        """Load persisted translation stats from disk on init."""
        import json
        try:
            if _TRANSLATION_STATS_FILE.exists():
                with open(_TRANSLATION_STATS_FILE, "r",
                          encoding="utf-8") as f:
                    data = json.load(f)
                counts = data.get("translation_counts", {})
                # Merge with defaults for forward compatibility
                for key in self._translation_counts:
                    if key in counts:
                        self._translation_counts[key] = (
                            counts[key])
                # Load any extra keys too
                for key, val in counts.items():
                    if key not in self._translation_counts:
                        self._translation_counts[key] = val
                lang = data.get("language_counts", {})
                for code, stats in lang.items():
                    self._language_counts[code] = {
                        "count": stats.get("count", 0),
                        "failed": stats.get("failed", 0),
                    }
                logger.info(
                    "Loaded translation stats from disk: "
                    "%d total",
                    sum(self._translation_counts.values()),
                )
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(
                "Could not load translation stats: %s", e)


# ── Item 1 (Phase 9): Stats file path ─────────────────────
# Moved from data/ (gitignored risk) to backend/app/state/
# (deployment-safe, __file__-relative works from any CWD)
from pathlib import Path
_TRANSLATION_STATS_FILE = (
    Path(__file__).resolve().parent / "state" / "translation_stats.json"
)

# ── Module-level singleton ─────────────────────────────────
metrics_store = MetricsStore()
# Load persisted stats on module import
metrics_store._load_translation_stats()
