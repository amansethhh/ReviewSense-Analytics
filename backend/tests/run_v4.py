import requests, time, io

BASE = "http://localhost:8001"
reviews = ["Review {}: {}".format(i, "great product!" if i % 2 == 0 else "terrible service!") for i in range(30)]
csv_content = "review\n" + "\n".join('"{}"'.format(r) for r in reviews)
files = {"file": ("counter_test.csv", io.StringIO(csv_content), "text/csv")}
data = {"text_column": "review", "model": "best"}

resp = requests.post("{}/bulk".format(BASE), files=files, data=data)
assert resp.status_code == 200, "FAIL: {} {}".format(resp.status_code, resp.text)
job_id = resp.json()["job_id"]
print("Job: {}".format(job_id))

prev, increments, start = 0, 0, time.time()
for _ in range(200):
    time.sleep(0.3)
    job = requests.get("{}/bulk/status/{}".format(BASE, job_id)).json()
    processed = job.get("processed", 0)
    if processed > prev:
        increments += 1
        elapsed = time.time() - start
        print("[{:.1f}s] INCREMENT #{}: {} -> {}".format(elapsed, increments, prev, processed))
        prev = processed
    if job["status"] == "completed":
        elapsed = time.time() - start
        print("\nDone in {:.1f}s | Total increments: {}".format(elapsed, increments))
        if increments >= 10:
            print("V4 PASS")
        else:
            print("V4 FAIL -- only {} increments (need >=10)".format(increments))
        break
    elif job["status"] == "failed":
        print("FAIL: {}".format(job.get("error")))
        break
else:
    print("TIMEOUT")
