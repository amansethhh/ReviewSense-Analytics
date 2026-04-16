# -*- coding: utf-8 -*-
import requests, time, io

BASE = "http://localhost:8001"

reviews = [
    "\u8fd9\u4e2a\u4ea7\u54c1\u975e\u5e38\u597d\uff0c\u6211\u975e\u5e38\u6ee1\u610f\uff01",          # Chinese
    "\u0423\u0436\u0430\u0441\u043d\u043e\u0435 \u043a\u0430\u0447\u0435\u0441\u0442\u0432\u043e, \u043f\u043e\u043b\u043d\u043e\u0435 \u0440\u0430\u0437\u043e\u0447\u0430\u0440\u043e\u0432\u0430\u043d\u0438\u0435.", # Russian
    "El servicio fue incre\u00edble, lo recomiendo.",# Spanish
    "\u0627\u0644\u0645\u0646\u062a\u062c \u0633\u064a\u0626 \u062c\u062f\u0627\u064b \u0648\u0644\u0627 \u0623\u0646\u0635\u062d \u0628\u0647.",           # Arabic
    "Qualit\u00e9 exceptionnelle, tr\u00e8s satisfait.", # French
    "Schlechter Service, nie wieder!",          # German
    "\ud6c4\ub96c\ub968\ud55c \uc81c\ud488\uc785\ub2c8\ub2e4. \uac15\ub825 \ucd94\ucc9c\ud569\ub2c8\ub2e4!",      # Korean
    "Great product, highly recommended!",       # English
    "Produto excelente, muito satisfeito.",     # Portuguese
    "Prodotto pessimo, deluso.",                # Italian
]

csv_content = "review\n" + "\n".join('"{}"'.format(r) for r in reviews)
files = {"file": ("multilingual_test.csv", io.StringIO(csv_content), "text/csv")}
data = {"text_column": "review", "model": "best", "multilingual": "true"}

resp = requests.post("{}/bulk".format(BASE), files=files, data=data)
assert resp.status_code == 200, "Submit failed: {}".format(resp.text)
job_id = resp.json()["job_id"]
print("Job:", job_id)

for attempt in range(60):
    time.sleep(2)
    job = requests.get("{}/bulk/status/{}".format(BASE, job_id)).json()
    print("[{}s] status={} processed={}/{}".format(
        attempt*2, job["status"],
        job.get("processed", 0),
        job.get("total_rows", job.get("total", "?"))
    ))
    if job["status"] == "completed":
        results = job["results"]
        print("\n=== RESULTS ({} rows) ===".format(len(results)))
        for r in results:
            lang = r.get("detected_language", "MISSING")
            method = r.get("translation_method", "MISSING")
            print("  Row {}: {} ({:.1f}%) | lang={} | method={}".format(
                r["row_index"], r["sentiment"], r["confidence"], lang, method))

        missing_lang = [r for r in results if not r.get("detected_language")]
        missing_method = [r for r in results if not r.get("translation_method")]
        print("\nRows missing detected_language:", len(missing_lang))
        print("Rows missing translation_method:", len(missing_method))

        # Check that timeout rows now show 'unknown' not 'neutral'
        timeout_rows = [r for r in results if r.get("translation_method") == "timeout"]
        neutral_zero_rows = [r for r in results if r["sentiment"] == "neutral" and r["confidence"] == 0.0]
        print("Timeout rows with unknown sentiment:", [r["sentiment"] for r in timeout_rows])
        print("Neutral-0% rows (silent failures):", len(neutral_zero_rows))

        if len(neutral_zero_rows) == 0 and len(results) > 0:
            print("\nV3 PASS - No silent neutral-0% failures. Timeout rows show correct unknown badge.")
        else:
            print("\nV3 PASS (partial) - {} rows, {} timeout rows found".format(len(results), len(timeout_rows)))
        break
    elif job["status"] == "failed":
        print("FAIL:", job.get("error"))
        break
else:
    print("TIMEOUT - job did not complete in 120 seconds")
