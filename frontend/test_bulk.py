import requests
import time

r = requests.post(
    "http://localhost:8000/bulk",
    files={"file": open("backend/tests/bulk_test.csv", "rb")},
    data={
        "text_column": "text",
        "model": "best",
        "run_absa": "false",
        "run_sarcasm": "true",
    },
)
data = r.json()
job_id = data["job_id"]
print(f"Job submitted: {job_id}")

while True:
    s = requests.get(f"http://localhost:8000/bulk/status/{job_id}").json()
    status = s["status"]
    processed = s.get("processed", 0)
    total = s.get("total_rows", "?")
    print(f"  Status: {status} | Processed: {processed} / {total}")
    if status in ("completed", "failed"):
        break
    time.sleep(2)

if status == "completed":
    sm = s["summary"]
    print(f"\n=== SUMMARY ===")
    print(f"Total Analyzed: {sm['total_analyzed']}")
    print(f"Positive %: {sm['positive_pct']}")
    print(f"Negative %: {sm['negative_pct']}")
    print(f"Neutral %: {sm['neutral_pct']}")
    print(f"Sarcasm Count: {sm.get('sarcasm_count', 0)}")
    print(f"\n=== ROWS ===")
    for row in s["results"]:
        idx = row["row_index"]
        sent = row["sentiment"]
        conf = row["confidence"]
        sarc = row.get("sarcasm_detected", False)
        text = row["text"][:60]
        print(f"  [{idx:2d}] {sent:8s} {conf:5.1f}% sarcasm={sarc} | {text}")
else:
    print(f"FAILED: {s.get('error', 'unknown')}")
