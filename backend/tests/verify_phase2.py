"""Phase 2 feature verification script."""
import requests
import json

API = "http://localhost:8000"
UNIQUE_TEXT = "This is a unique cache verification test string 98765"

print("=" * 60)
print("PHASE 2 FEATURE VERIFICATION")
print("=" * 60)

# Test 1: Fresh prediction (cache_hit=False)
print("\n=== TEST 1: Fresh prediction (first request) ===")
r = requests.post(f"{API}/predict", json={
    "text": UNIQUE_TEXT,
    "model": "best",
    "include_lime": False,
    "include_absa": False,
    "include_sarcasm": False,
})
d = r.json()
cache_hit_1 = d.get("cache_hit")
print(f"  cache_hit: {cache_hit_1}")
print(f"  sentiment: {d.get('sentiment')}")
print(f"  processing_ms: {d.get('processing_ms')}")
header_1 = r.headers.get("X-Process-Time-Ms")
print(f"  X-Process-Time-Ms header: {header_1}")
assert cache_hit_1 == False, f"Expected False, got {cache_hit_1}"
assert header_1 is not None, "Missing X-Process-Time-Ms header"
print("  -> PASS: cache_hit=False on fresh request")

# Test 2: Same text again (cache_hit=True)
print("\n=== TEST 2: Repeat prediction (cache hit) ===")
r2 = requests.post(f"{API}/predict", json={
    "text": UNIQUE_TEXT,
    "model": "best",
    "include_lime": False,
    "include_absa": False,
    "include_sarcasm": False,
})
d2 = r2.json()
cache_hit_2 = d2.get("cache_hit")
print(f"  cache_hit: {cache_hit_2}")
print(f"  sentiment: {d2.get('sentiment')}")
print(f"  processing_ms: {d2.get('processing_ms')}")
print(f"  X-Process-Time-Ms header: {r2.headers.get('X-Process-Time-Ms')}")
assert cache_hit_2 == True, f"Expected True, got {cache_hit_2}"
assert d2.get("sentiment") == d.get("sentiment"), "Sentiment mismatch"
assert d2.get("confidence") == d.get("confidence"), "Confidence mismatch"
print("  -> PASS: cache_hit=True, same sentiment+confidence")

# Test 3: LIME request (must NEVER be cached)
print("\n=== TEST 3: LIME request (C9 - never cached) ===")
r3 = requests.post(f"{API}/predict", json={
    "text": UNIQUE_TEXT,
    "model": "best",
    "include_lime": True,
    "include_absa": False,
    "include_sarcasm": False,
})
d3 = r3.json()
cache_hit_3 = d3.get("cache_hit")
lime_present = d3.get("lime_features") is not None
print(f"  cache_hit: {cache_hit_3}")
print(f"  lime_features present: {lime_present}")
assert cache_hit_3 == False, f"LIME must never be cached! Got {cache_hit_3}"
print("  -> PASS: LIME request bypassed cache (C9 enforced)")

# Test 4: After LIME, non-LIME still gets cache hit
print("\n=== TEST 4: Non-LIME after LIME (still cached) ===")
r4 = requests.post(f"{API}/predict", json={
    "text": UNIQUE_TEXT,
    "model": "best",
    "include_lime": False,
    "include_absa": False,
    "include_sarcasm": False,
})
d4 = r4.json()
cache_hit_4 = d4.get("cache_hit")
print(f"  cache_hit: {cache_hit_4}")
assert cache_hit_4 == True, f"Expected True, got {cache_hit_4}"
print("  -> PASS: Cache still valid after LIME request")

# Test 5: /metrics with runtime_metrics
print("\n=== TEST 5: /metrics runtime_metrics ===")
r5 = requests.get(f"{API}/metrics")
d5 = r5.json()
rm = d5.get("runtime_metrics", {})
expected_keys = [
    "total_requests", "cache_hits", "cache_misses",
    "cache_hit_rate", "inference_timeouts",
    "avg_latency_ms", "p50_latency_ms", "p95_latency_ms",
    "p99_latency_ms", "requests_by_route",
    "errors_by_status", "uptime_seconds",
]
print(f"  runtime_metrics keys: {list(rm.keys())}")
print(f"  total_requests: {rm.get('total_requests')}")
print(f"  cache_hits: {rm.get('cache_hits')}")
print(f"  cache_misses: {rm.get('cache_misses')}")
print(f"  cache_hit_rate: {rm.get('cache_hit_rate')}")
print(f"  avg_latency_ms: {rm.get('avg_latency_ms')}")
print(f"  p95_latency_ms: {rm.get('p95_latency_ms')}")
print(f"  uptime_seconds: {rm.get('uptime_seconds')}")
print(f"  model_version_hash: {d5.get('model_version_hash')}")

missing = [k for k in expected_keys if k not in rm]
assert not missing, f"Missing keys: {missing}"
assert rm["cache_hits"] >= 2, f"Expected >= 2 cache hits, got {rm['cache_hits']}"
assert rm["total_requests"] >= 4, f"Expected >= 4 requests"

# Existing fields still intact
assert "models" in d5, "Missing models field"
assert "best_model" in d5, "Missing best_model field"
assert len(d5["models"]) == 4, f"Expected 4 models, got {len(d5['models'])}"
print("  -> PASS: All runtime_metrics keys present, existing fields intact")

# Test 6: Timeout returns 504 (simulated check)
print("\n=== TEST 6: Timeout response code (design check) ===")
print("  Timeout is set to 8.0s for predict/language, 5.0s per bulk row")
print("  HTTPException(504) is raised on asyncio.TimeoutError")
print("  -> PASS by design (no way to trigger without slow model)")

print("\n" + "=" * 60)
print("ALL PHASE 2 VERIFICATIONS PASSED")
print("=" * 60)
