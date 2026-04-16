"""
O9: Adaptive Performance Tuning

Central module for runtime-adaptive resource management.

Mechanisms:
1. AdaptiveBatchSizer  — Dynamic batch size based on CPU/memory load
2. DynamicWorkerPool   — Auto-detect CPU cores for ThreadPoolExecutor
3. RequestDeduplicator — Coalesce identical concurrent async requests
4. InferenceThrottler  — Semaphore-based concurrency limiter for ML

No new hard dependencies. Uses psutil if available (common transitive
dep of ML packages), falls back to conservative static defaults.

Phase 2 update (Part 3): Deduplicator fail-safe — waiter-side
timeout with asyncio.wait_for + asyncio.shield so a stuck owner
doesn't hang all waiters indefinitely.
"""

import os
import asyncio
import hashlib
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Awaitable, Callable

logger = logging.getLogger("reviewsense.adaptive")

# ── psutil optional import ─────────────────────────────────
try:
    import psutil
    _HAS_PSUTIL = True
except ImportError:
    _HAS_PSUTIL = False
    logger.info(
        "psutil not available — using static defaults "
        "for adaptive tuning"
    )


# ── 1. Adaptive Batch Sizer ───────────────────────────────

class AdaptiveBatchSizer:
    """
    Dynamically adjusts batch size for bulk processing based
    on current CPU and memory usage.

    Range: [min_size, max_size], default: default_size.
    Uses exponential moving average (EMA) to smooth transitions
    and prevent oscillation.

    Thread-safe — designed to be called from background threads.
    """

    def __init__(
        self,
        min_size: int = 10,
        max_size: int = 50,
        default_size: int = 25,
        alpha: float = 0.3,
    ) -> None:
        self._min: int = min_size
        self._max: int = max_size
        self._current: float = float(default_size)
        self._alpha: float = alpha
        self._lock: threading.Lock = threading.Lock()
        self._last_cpu: float = 50.0
        self._last_mem: float = 50.0
        logger.info(
            f"AdaptiveBatchSizer initialized: "
            f"range=[{min_size}, {max_size}], "
            f"default={default_size}"
        )

    def get_batch_size(self) -> int:
        """
        Sample current system load and return an adaptive
        batch size. Uses EMA smoothing to avoid oscillation.
        """
        cpu, mem = self._sample_load()
        with self._lock:
            self._last_cpu = cpu
            self._last_mem = mem
            target = self._compute_target(cpu, mem)
            # EMA smoothing
            self._current = (
                self._alpha * target
                + (1.0 - self._alpha) * self._current
            )
            self._current = max(
                float(self._min),
                min(float(self._max), self._current),
            )
            result = int(self._current)
        return result

    def should_throttle(self) -> bool:
        """
        Returns True if system is under heavy load and
        bulk processing should insert a brief pause.
        """
        with self._lock:
            return (
                self._last_cpu > 85.0
                or self._last_mem > 90.0
            )

    def _sample_load(self) -> tuple[float, float]:
        """
        Get current CPU% and memory%. Uses psutil if available,
        otherwise returns conservative defaults (50%, 50%).
        """
        if _HAS_PSUTIL:
            try:
                cpu = psutil.cpu_percent(interval=0)
                mem = psutil.virtual_memory().percent
                return cpu, mem
            except Exception:
                pass
        return 50.0, 50.0

    def _compute_target(
        self, cpu: float, mem: float
    ) -> float:
        """
        Compute target batch size based on system load.
        High load → small batches. Low load → large batches.
        """
        if mem > 85.0 or cpu > 80.0:
            return float(self._min)
        elif cpu < 40.0 and mem < 60.0:
            return float(self._max)
        else:
            # Linear interpolation based on CPU headroom
            factor = 1.0 - (cpu / 100.0)
            return float(self._min) + (
                float(self._max - self._min) * factor
            )


# ── 2. Dynamic Worker Pool ─────────────────────────────────

class DynamicWorkerPool:
    """
    ThreadPoolExecutor wrapper that auto-detects optimal
    worker count based on available CPU cores, capped at
    max_cap (Render free tier constraint = 4).

    On Render (1-2 cores): min(2, 4) = 2 workers
    On dev machines (8+ cores): min(8, 4) = 4 workers
    """

    def __init__(
        self,
        max_cap: int = 4,
        name: str = "default",
    ) -> None:
        cores: int = os.cpu_count() or 2
        self._max_workers: int = min(cores, max_cap)
        self._executor: ThreadPoolExecutor = ThreadPoolExecutor(
            max_workers=self._max_workers,
            thread_name_prefix=f"ml-{name}",
        )
        logger.info(
            f"DynamicWorkerPool '{name}': "
            f"cores={cores}, workers={self._max_workers} "
            f"(cap={max_cap})"
        )

    @property
    def executor(self) -> ThreadPoolExecutor:
        """Return the underlying ThreadPoolExecutor."""
        return self._executor

    @property
    def max_workers(self) -> int:
        """Return the number of workers allocated."""
        return self._max_workers


# ── 3. Request Deduplicator ────────────────────────────────

class RequestDeduplicator:
    """
    Async-safe request coalescing. If an identical request
    is already in-flight, new callers await the same Future
    instead of running a duplicate computation.

    Key = hash(text + model + options). Max concurrent keys
    bounded to prevent unbounded memory growth.

    Phase 2 fail-safe (Part 3):
      - Waiters use asyncio.wait_for(shield(future), timeout=10s)
      - On timeout, waiters fall back to fresh execution
        instead of hanging indefinitely
      - Owners always clean up via try/finally
      - Exceptions are propagated to waiters via
        future.set_exception()

    Usage:
        key = deduplicator.make_key(text, model)
        result = await deduplicator.deduplicate(key, coro_fn)
    """

    def __init__(self, max_keys: int = 512) -> None:
        self._in_flight: dict[str, asyncio.Future] = {}
        self._lock: asyncio.Lock = asyncio.Lock()
        self._max_keys: int = max_keys
        self._dedup_hits: int = 0
        self._total_calls: int = 0
        logger.info(
            f"RequestDeduplicator initialized: "
            f"max_keys={max_keys}"
        )

    @staticmethod
    def make_key(*parts: str) -> str:
        """Create a dedup key from variable parts."""
        raw = ":".join(parts)
        return hashlib.md5(
            raw.encode("utf-8")
        ).hexdigest()

    async def deduplicate(
        self,
        key: str,
        coro_factory: Callable[[], Awaitable[Any]],
    ) -> Any:
        """
        If key is in-flight, await the existing Future
        (with 10s timeout fail-safe). Otherwise, run
        coro_factory() and share the result.

        If max_keys is exceeded, falls through to direct
        execution (no dedup) to bound memory.

        Fail-safe guarantees:
          - Owner ALWAYS cleans up key via try/finally
          - Waiter times out after 10s → fresh execution
          - Exceptions from owner propagate to all waiters
        """
        self._total_calls += 1

        async with self._lock:
            if key in self._in_flight:
                # Another request with same key is in-flight
                future = self._in_flight[key]
                is_owner = False
                self._dedup_hits += 1
                logger.debug(
                    f"Dedup HIT: key={key[:8]}... "
                    f"(hits={self._dedup_hits}"
                    f"/{self._total_calls})"
                )
            elif len(self._in_flight) >= self._max_keys:
                # Overflow — skip dedup, run directly
                logger.debug(
                    f"Dedup OVERFLOW: "
                    f"{len(self._in_flight)} keys, "
                    f"running directly"
                )
                return await coro_factory()
            else:
                # We are the owner — create Future and run
                loop = asyncio.get_running_loop()
                future = loop.create_future()
                self._in_flight[key] = future
                is_owner = True

        if is_owner:
            # Owner path: run inference, share result
            try:
                result = await coro_factory()
                future.set_result(result)
                return result
            except asyncio.CancelledError:
                future.cancel()
                raise
            except Exception as e:
                future.set_exception(e)
                raise
            finally:
                # ALWAYS clean up — prevents leaked keys
                async with self._lock:
                    self._in_flight.pop(key, None)
        else:
            # Waiter path: await owner's Future with timeout
            # asyncio.shield prevents our timeout from
            # cancelling the owner's computation
            try:
                return await asyncio.wait_for(
                    asyncio.shield(future),
                    timeout=10.0,
                )
            except asyncio.TimeoutError:
                logger.warning(
                    f"Dedup timeout for key {key[:8]}... "
                    "— falling back to fresh execution"
                )
                return await coro_factory()

    @property
    def stats(self) -> dict[str, int]:
        """Return dedup hit statistics."""
        return {
            "total_calls": self._total_calls,
            "dedup_hits": self._dedup_hits,
            "in_flight": len(self._in_flight),
        }


# ── 4. Inference Throttler ─────────────────────────────────

class InferenceThrottler:
    """
    asyncio.Semaphore-based concurrency limiter for ML
    inference. Prevents thread pool exhaustion when bulk +
    concurrent single predictions run simultaneously.

    Callers beyond the limit queue transparently — no 429
    errors, just backpressure until a slot is available.

    Usage:
        async with throttler:
            result = await loop.run_in_executor(...)
    """

    def __init__(self, max_concurrent: int = 8) -> None:
        self._semaphore: asyncio.Semaphore = (
            asyncio.Semaphore(max_concurrent)
        )
        self._max: int = max_concurrent
        self._active: int = 0
        logger.info(
            f"InferenceThrottler initialized: "
            f"max_concurrent={max_concurrent}"
        )

    async def __aenter__(self) -> "InferenceThrottler":
        await self._semaphore.acquire()
        self._active += 1
        return self

    async def __aexit__(
        self,
        exc_type: Any,
        exc_val: Any,
        exc_tb: Any,
    ) -> bool:
        self._semaphore.release()
        self._active -= 1
        return False

    @property
    def active_count(self) -> int:
        """Number of currently active inference calls."""
        return self._active

    @property
    def max_concurrent(self) -> int:
        """Maximum allowed concurrent inference calls."""
        return self._max


# ── Module-level singletons ────────────────────────────────
# Instantiated once at import time, shared across all routes.

# Primary worker pool for request-driven ML inference
# (predict.py and language.py share this pool).
primary_pool = DynamicWorkerPool(
    max_cap=4, name="inference"
)

# Throttler: 2× pool workers for headroom under concurrent
# predict + language requests.
inference_throttler = InferenceThrottler(
    max_concurrent=2 * primary_pool.max_workers
)

# Deduplicator: coalesces identical concurrent predictions.
request_deduplicator = RequestDeduplicator(max_keys=512)

# Batch sizer: shared across bulk jobs for adaptive sizing.
adaptive_batch_sizer = AdaptiveBatchSizer(
    min_size=10, max_size=50, default_size=25
)
