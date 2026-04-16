"""Bulk E2E test script — tests the backend bulk analysis pipeline."""
import requests
import time

BASE = "http://localhost:8000"

# 1. Submit bulk job
print("=" * 60)
print("BULK E2E TEST")
print("=" * 60)

with open("backend/tests/bulk_test.csv", "rb") as f:
    r = requests.post(
        f"{BASE}/bulk/",
        files={"file": ("bulk_test.csv", f, "text/csv")},
        data={
            "text_column": "text",
            "model": "best",
            "run_absa": "false",
            "run_sarcasm": "true",
        },
    )
    print(f"Submit response: {r.status_code}")
    submit = r.json()
    job_id = submit.get("job_id")
    print(f"Job ID: {job_id}")

# 2. Poll for completion
for i in range(30):
    time.sleep(2)
    status = requests.get(f"{BASE}/bulk/status/{job_id}").json()
    processed = status.get("processed", 0)
    total = status.get("total_rows", "?")
    st = status["status"]
    print(f"  Poll {i+1}: status={st}, processed={processed}/{total}")
    if st in ("completed", "failed"):
        break

# 3. Print results
print()
if status["status"] == "completed":
    summary = status.get("summary", {})
    print("RESULTS:")
    print(f"  Total Analyzed: {summary.get('total_analyzed')}")
    print(f"  Positive: {summary.get('positive_pct')}%")
    print(f"  Negative: {summary.get('negative_pct')}%")
    print(f"  Neutral:  {summary.get('neutral_pct')}%")
    print(f"  Sarcasm Count: {summary.get('sarcasm_count')}")

    results = status.get("results", [])
    print(f"\n  Result rows: {len(results)}")
    for row in results:
        sarcasm = row.get("sarcasm_detected", "N/A")
        print(
            f"    Row {row['row_index']}: "
            f"{row['sentiment']} "
            f"({row['confidence']:.1f}%) "
            f"pol={row['polarity']:.3f} "
            f"sarcasm={sarcasm}"
        )
    print("\n✅ BULK E2E TEST PASSED")
else:
    print(f"❌ Job failed: {status.get('error')}")
