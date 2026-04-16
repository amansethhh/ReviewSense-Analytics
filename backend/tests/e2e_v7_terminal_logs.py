"""
Phase 6 GAP 3: E2E V7 — Prove that backend logs are appended in real-time
per-row and that the polling API delivers them progressively.

Pass criteria:
  - >= 3 distinct log-snapshot ticks (backend delivered new logs at 3+ polls)
  - >= 10 unique log lines seen in total
  - Final verdict: V7 PASS
"""
import requests
import time
import io

BASE = "http://localhost:8000"

reviews = [
    "Review number {}: {}".format(i, "great!" if i % 2 == 0 else "terrible!")
    for i in range(20)
]
csv_content = "review\n" + "\n".join('"{}"'.format(r) for r in reviews)
files = {
    "file": ("terminal_test.csv", io.StringIO(csv_content), "text/csv")
}
data = {"text_column": "review", "model": "best"}

resp = requests.post("{}/bulk".format(BASE), files=files, data=data)
assert resp.status_code == 200, "Submit failed: {}".format(resp.text)
job_id = resp.json()["job_id"]
print("Job: {}".format(job_id))

all_logs_seen: set = set()
snapshots = []

for tick in range(60):
    time.sleep(1)
    job = requests.get("{}/bulk/status/{}".format(BASE, job_id)).json()
    current_logs = job.get("logs", [])
    new_logs = [ln for ln in current_logs if ln not in all_logs_seen]
    if new_logs:
        all_logs_seen.update(new_logs)
        snapshots.append({
            "tick": tick,
            "processed": job.get("processed", 0),
            "new_log_count": len(new_logs),
            "sample": new_logs[-1],
        })
    if job["status"] == "completed":
        break
    elif job["status"] == "failed":
        print("FAIL: {}".format(job))
        raise SystemExit(1)

print("\nTotal log snapshots captured: {}".format(len(snapshots)))
print("Total unique log lines seen:  {}".format(len(all_logs_seen)))
print("\nSnapshot sequence:")
for s in snapshots:
    print("  [tick {:2d}] processed={:3d}  +{} logs | last: {}".format(
        s["tick"], s["processed"], s["new_log_count"], s["sample"]))

if len(snapshots) >= 3 and len(all_logs_seen) >= 10:
    print("\nV7 PASS — logs are being appended in real-time")
else:
    print(
        "\nV7 FAIL — only {} snapshots and {} unique logs "
        "(need >=3 and >=10)".format(len(snapshots), len(all_logs_seen))
    )
    raise SystemExit(1)
