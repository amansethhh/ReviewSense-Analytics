import requests, time, io, uuid

BASE = "http://localhost:8000"

# Mix of languages to force translation (slower processing)
templates_pos = [
    "Este producto es absolutamente fantástico y me encanta todo",  # Spanish
    "Dieses Produkt ist absolut fantastisch und ich liebe es",     # German
    "Ce produit est absolument fantastique et je l'adore",         # French
    "Questo prodotto è assolutamente fantastico e lo adoro",       # Italian
    "Este produto é absolutamente fantástico e eu adoro",          # Portuguese
]
templates_neg = [
    "Este producto es terrible, una pérdida de dinero completa",   # Spanish
    "Dieses Produkt ist schrecklich, eine totale Geldverschwendung",# German
    "Ce produit est terrible, un gaspillage d'argent total",       # French
    "Questo prodotto è terribile, uno spreco di soldi totale",     # Italian
    "Este produto é terrível, um desperdício de dinheiro total",   # Portuguese
]

reviews = []
for i in range(100):
    uid = uuid.uuid4().hex[:6]
    if i % 2 == 0:
        reviews.append(f"{templates_pos[i % len(templates_pos)]} {uid}")
    else:
        reviews.append(f"{templates_neg[i % len(templates_neg)]} {uid}")

csv_content = "review\n" + "\n".join(f'"{r}"' for r in reviews)
files = {"file": ("counter_test.csv", io.StringIO(csv_content), "text/csv")}
data = {"text_column": "review", "model": "best", "multilingual": "true"}

resp = requests.post(f"{BASE}/bulk", files=files, data=data)
assert resp.status_code == 200, f"Submit failed: {resp.text}"
job_id = resp.json()["job_id"]
print(f"Job: {job_id}")

prev_processed = 0
increment_count = 0
start = time.time()

for _ in range(300):
    time.sleep(0.2)
    status_resp = requests.get(f"{BASE}/bulk/status/{job_id}")
    job = status_resp.json()
    processed = job.get("processed", 0)
    elapsed = time.time() - start
    
    if processed > prev_processed:
        increment_count += 1
        print(f"[{elapsed:.1f}s] INCREMENT {increment_count}: {prev_processed} -> {processed}")
        prev_processed = processed
    
    if job["status"] == "completed":
        print(f"\nCompleted in {elapsed:.1f}s | Total increments seen: {increment_count}")
        assert increment_count >= 10, f"FAIL: only {increment_count} increments seen (need >=10)"
        print("V4 PASS - counter incremented in real-time")
        break
    elif job["status"] == "failed":
        print(f"FAIL: {job.get('error')}")
        break
else:
    print("TIMEOUT")
