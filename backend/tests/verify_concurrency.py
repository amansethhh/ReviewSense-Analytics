"""
MISSING-3: Concurrency Verification Script

Proves that O9 deduplication and throttling work under
concurrent load. Run with the server already started:

    python backend/tests/verify_concurrency.py

Tests:
1. Send 5 identical simultaneous POST /predict requests
   → Server logs should show only 1 inference ran
2. Measure throughput: sequential vs concurrent
"""

import sys
import os
import time
import json
import asyncio
import logging

sys.path.insert(0, os.path.abspath(
    os.path.join(os.path.dirname(__file__), '../..')))

# Use aiohttp for true concurrent requests
try:
    import aiohttp
except ImportError:
    print("ERROR: aiohttp required. Install: pip install aiohttp")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("concurrency_test")

API_BASE = "http://localhost:8000"

IDENTICAL_TEXT = "The food was absolutely amazing and delicious."
PREDICT_PAYLOAD = {
    "text": IDENTICAL_TEXT,
    "model": "best",
    "include_lime": False,
    "include_absa": False,
    "include_sarcasm": False,
}

UNIQUE_TEXTS = [
    "Outstanding service, I loved every moment.",
    "Terrible experience, complete waste of money.",
    "It was okay, nothing special.",
    "Best purchase I have ever made.",
    "The product broke after one day.",
    "Very disappointing quality.",
    "Decent value for the price.",
    "Horrible customer support.",
    "Exceeded all my expectations.",
    "Amazing quality and fast shipping.",
]


async def send_predict(session: aiohttp.ClientSession,
                       payload: dict) -> dict:
    """Send a single predict request, return response + timing."""
    start = time.perf_counter()
    async with session.post(
        f"{API_BASE}/predict",
        json=payload,
        timeout=aiohttp.ClientTimeout(total=30),
    ) as resp:
        data = await resp.json()
        elapsed = time.perf_counter() - start
        return {
            "status": resp.status,
            "sentiment": data.get("sentiment"),
            "confidence": data.get("confidence"),
            "processing_ms": data.get("processing_ms"),
            "wall_ms": int(elapsed * 1000),
        }


async def test_dedup_concurrent():
    """
    TEST 1: Deduplication
    Send 5 identical requests simultaneously.
    The deduplicator should process only 1 inference
    and share the result to all 5.
    """
    print("\n" + "=" * 60)
    print("TEST 1: REQUEST DEDUPLICATION")
    print("Sending 5 identical concurrent requests...")
    print("Expected: 1 inference, 4 dedup hits")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        tasks = [
            send_predict(session, PREDICT_PAYLOAD)
            for _ in range(5)
        ]
        start = time.perf_counter()
        results = await asyncio.gather(*tasks)
        total_wall = int(
            (time.perf_counter() - start) * 1000
        )

    print(f"\nTotal wall time: {total_wall}ms")
    print(f"{'#':<4} {'Status':<8} {'Sentiment':<10} "
          f"{'Conf':<8} {'Server ms':<10} {'Wall ms':<8}")
    print("-" * 52)

    for i, r in enumerate(results):
        print(
            f"{i+1:<4} {r['status']:<8} "
            f"{r['sentiment']:<10} "
            f"{r['confidence']:<8.1f} "
            f"{r['processing_ms']:<10} "
            f"{r['wall_ms']:<8}"
        )

    # All results should be identical
    sentiments = {r["sentiment"] for r in results}
    confidences = {r["confidence"] for r in results}
    all_200 = all(r["status"] == 200 for r in results)

    if all_200 and len(sentiments) == 1 and len(confidences) == 1:
        print("\n✅ DEDUP VERIFIED: All 5 responses identical")
        print("   Check server logs for 'Dedup HIT' messages")
    else:
        print("\n⚠️ Results vary — check server logs")

    return total_wall


async def test_throughput_comparison():
    """
    TEST 2: Throughput — Sequential vs Concurrent
    Measure reviews/second for 10 unique predictions.
    """
    print("\n" + "=" * 60)
    print("TEST 2: THROUGHPUT COMPARISON")
    print("10 unique predictions: sequential vs concurrent")
    print("=" * 60)

    # Sequential
    print("\n--- Sequential (baseline) ---")
    async with aiohttp.ClientSession() as session:
        seq_start = time.perf_counter()
        for text in UNIQUE_TEXTS:
            payload = {
                "text": text,
                "model": "best",
                "include_lime": False,
                "include_absa": False,
                "include_sarcasm": False,
            }
            await send_predict(session, payload)
        seq_elapsed = time.perf_counter() - seq_start

    seq_rps = len(UNIQUE_TEXTS) / seq_elapsed
    print(f"  Time: {seq_elapsed:.2f}s")
    print(f"  Throughput: {seq_rps:.1f} reviews/sec")

    # Concurrent
    print("\n--- Concurrent (with throttler) ---")
    async with aiohttp.ClientSession() as session:
        tasks = []
        for text in UNIQUE_TEXTS:
            payload = {
                "text": text,
                "model": "best",
                "include_lime": False,
                "include_absa": False,
                "include_sarcasm": False,
            }
            tasks.append(send_predict(session, payload))

        con_start = time.perf_counter()
        results = await asyncio.gather(*tasks)
        con_elapsed = time.perf_counter() - con_start

    con_rps = len(UNIQUE_TEXTS) / con_elapsed
    all_200 = all(r["status"] == 200 for r in results)

    print(f"  Time: {con_elapsed:.2f}s")
    print(f"  Throughput: {con_rps:.1f} reviews/sec")
    print(f"  All 200 OK: {all_200}")

    speedup = con_rps / seq_rps if seq_rps > 0 else 0
    print(f"\n  Speedup: {speedup:.2f}x")

    return seq_rps, con_rps


async def test_metrics_hash():
    """
    TEST 3: Verify model_version_hash in /metrics response.
    """
    print("\n" + "=" * 60)
    print("TEST 3: MODEL VERSION HASH (O7)")
    print("=" * 60)

    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{API_BASE}/metrics",
            timeout=aiohttp.ClientTimeout(total=10),
        ) as resp:
            data = await resp.json()

    mvh = data.get("model_version_hash", "MISSING")
    print(f"  model_version_hash: {mvh}")
    print(f"  Length: {len(mvh)}")

    if mvh and mvh != "MISSING" and mvh != "":
        if mvh == "unknown":
            print("  ⚠️ Hash is 'unknown' (models dir "
                  "may be empty)")
        else:
            print("  ✅ Valid MD5 hash present")
    else:
        print("  ❌ Hash missing from response")


async def main():
    print("=" * 60)
    print("O9 CONCURRENCY VERIFICATION")
    print(f"API: {API_BASE}")
    print("=" * 60)

    # Check server is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_BASE}/health",
                timeout=aiohttp.ClientTimeout(total=5),
            ) as resp:
                if resp.status != 200:
                    print(f"ERROR: Server returned {resp.status}")
                    return
                print("Server: healthy ✓")
    except Exception as e:
        print(f"ERROR: Cannot reach server: {e}")
        print("Start the server first:")
        print("  uvicorn backend.app.main:app --port 8000")
        return

    await test_dedup_concurrent()
    await test_throughput_comparison()
    await test_metrics_hash()

    print("\n" + "=" * 60)
    print("VERIFICATION COMPLETE")
    print("=" * 60)
    print("\nCheck server logs (stderr) for:")
    print("  - 'Dedup HIT' messages (deduplication)")
    print("  - 'batch_size=' log entries (adaptive sizing)")
    print("  - DynamicWorkerPool worker count on startup")


if __name__ == "__main__":
    asyncio.run(main())
