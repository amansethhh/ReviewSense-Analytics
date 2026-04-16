"""Section E — Complete E2E validation script"""
import httpx, json, time, csv, io, sys
sys.stdout.reconfigure(encoding='utf-8')

BASE = "http://localhost:8000"
client = httpx.Client(timeout=60)

print("=" * 60)
print("[E5] Edge Case Accuracy via /language")
print("=" * 60)

cases = [
    ("not bad",                "neutral"),
    ("not terrible at all",    "neutral"),
    ("not awful",              "neutral"),
    ("Good product but overpriced",    "neutral"),
    ("Great food but slow service",    "neutral"),
    ("Amazing quality but expensive",  "neutral"),
    ("absolutely loved it",     "positive"),
    ("excellent service",       "positive"),
]

v1_passed = 0
for text, expected in cases:
    r = client.post(f"{BASE}/language", json={"text": text})
    d = r.json()
    got = d.get("sentiment", "ERROR")
    conf = d.get("confidence", 0)
    ok = got == expected
    if ok: v1_passed += 1
    tag = "PASS" if ok else f"FAIL (expected {expected})"
    print(f"  {tag} '{text}' -> {got} {conf:.1f}%")

print(f"\nEdge cases: {v1_passed}/{len(cases)} passed")

# Also test /predict with corrections applied
print("\n--- /predict corrections check ---")
for text in ["not bad", "not terrible at all", "Good product but overpriced"]:
    r = client.post(f"{BASE}/predict", json={
        "text": text, "include_lime": False,
        "include_absa": False, "include_sarcasm": False,
    })
    d = r.json()
    print(f"  /predict '{text}' -> {d['sentiment']} {d['confidence']:.1f}%")

print("\n" + "=" * 60)
print("[E6] Bulk Analysis E2E")
print("=" * 60)

rows = [
    "The food was absolutely amazing",
    "Terrible experience, waste of money",
    "It was okay, nothing special",
    "Not bad actually",
    "Good product but overpriced",
    "Outstanding service",
    "Very disappointing quality",
    "Not terrible at all",
    "Great quality but slow delivery",
    "Best purchase I ever made",
    "I would never buy this again",
    "",
    "Perfect in every way",
    "Horrible customer support",
    "Amazing quality and fast shipping",
    "Not awful for the price",
    "Exceeded all my expectations",
    "Good but expensive",
    "Five stars, absolutely love it",
    "The delivery was extremely slow",
]

buf = io.StringIO()
writer = csv.writer(buf)
writer.writerow(["review"])
for r in rows:
    writer.writerow([r])
csv_bytes = buf.getvalue().encode()

resp = client.post(f"{BASE}/bulk",
    files={"file": ("test.csv", csv_bytes, "text/csv")})
job = resp.json()
job_id = job["job_id"]
print(f"Job started: {job_id}")
print(f"Total rows: {job['total_rows']}")

prev_processed = -1
start = time.time()
while True:
    s = client.get(f"{BASE}/bulk/status/{job_id}").json()
    processed = s["processed"]
    total = s["total_rows"]
    status = s["status"]
    if processed != prev_processed:
        logs = s.get("logs", [])
        last_log = logs[-1] if logs else ""
        elapsed = int(time.time() - start)
        print(f"  [{elapsed}s] {processed}/{total} -- {last_log[:80]}")
        prev_processed = processed
    if status in ("completed", "failed"):
        print(f"\nFinal status: {status}")
        if status == "completed":
            results = s.get("results", [])
            summary = s.get("summary", {})
            print(f"Results: {len(results)} rows")
            print(f"Summary: {json.dumps(summary, indent=2)}")
            elapsed_total = time.time() - start
            print(f"Speed: {total / elapsed_total:.1f} rows/sec")
        break
    time.sleep(0.5)

print("\n" + "=" * 60)
print("[E8] Empty Row Handling")
print("=" * 60)

bad_rows = ["", "   ", "a" * 500, "good product"]
buf2 = io.StringIO()
csv.writer(buf2).writerows([["review"]] + [[r] for r in bad_rows])
resp2 = client.post(f"{BASE}/bulk",
    files={"file": ("bad.csv", buf2.getvalue().encode(), "text/csv")})
job_id2 = resp2.json()["job_id"]
print(f"Bad-rows job: {job_id2}")

while True:
    s2 = client.get(f"{BASE}/bulk/status/{job_id2}").json()
    if s2["status"] in ("completed", "failed"):
        print(f"Status: {s2['status']}")
        for r in s2.get("results", []):
            badge = "ERROR" if (r["confidence"] == 0 or r["sentiment"] == "unknown") else "OK"
            txt = r['text'][:30] if r['text'] else "(empty)"
            print(f"  Row {r['row_index']}: {badge} -- {r['sentiment']} {r['confidence']:.1f}% -- '{txt}'")
        break
    time.sleep(0.5)

print("\n" + "=" * 60)
print("[E9] Export CSV")
print("=" * 60)

resp_export = client.get(f"{BASE}/bulk/export/{job_id}")
print(f"Export status: {resp_export.status_code}")
if resp_export.status_code == 200:
    lines = resp_export.text.strip().split("\n")
    for line in lines[:5]:
        print(f"  {line}")
    print(f"  ... total {len(lines)} lines")
else:
    print(f"Export response: {resp_export.text[:200]}")

print("\n" + "=" * 60)
print("[E10] Feedback API")
print("=" * 60)

resp_fb = client.post(f"{BASE}/feedback/submit", json={
    "text": "test review",
    "predicted_sentiment": "positive",
    "correct_sentiment": "positive",
    "confidence": 90.0,
    "source": "test",
})
print(f"Feedback status: {resp_fb.status_code}")
print(f"Response: {resp_fb.json()}")

resp_stats = client.get(f"{BASE}/feedback/stats")
print(f"Stats: {resp_stats.json()}")

print("\n" + "=" * 60)
print("[E11] Translation Metrics")
print("=" * 60)

resp_tm = client.get(f"{BASE}/metrics/translations")
print(f"Status: {resp_tm.status_code}")
print(f"Response: {json.dumps(resp_tm.json(), indent=2)}")

print("\n" + "=" * 60)
print("ALL E2E CHECKS COMPLETE")
print("=" * 60)
