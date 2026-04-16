import requests, time, csv, io

BASE = "http://localhost:8000"

reviews = [
    "这个产品非常好，我非常满意！",          # Chinese
    "Ужасное качество, полное разочарование.", # Russian
    "El servicio fue increíble, lo recomiendo.",# Spanish
    "المنتج سيء جداً ولا أنصح به.",           # Arabic
    "Qualité exceptionnelle, très satisfait.", # French
    "Schlechter Service, nie wieder!",          # German
    "훌륭한 제품입니다. 강력 추천합니다!",      # Korean
    "Great product, highly recommended!",       # English
    "Produto excelente, muito satisfeito.",     # Portuguese
    "Prodotto pessimo, deluso.",                # Italian
]

csv_content = "review\n" + "\n".join(f'"{r}"' for r in reviews)
files = {"file": ("multilingual_test.csv", io.StringIO(csv_content), "text/csv")}
data = {"text_column": "review", "model": "best", "multilingual": "true"}

resp = requests.post(f"{BASE}/bulk", files=files, data=data)
assert resp.status_code == 200, f"Submit failed: {resp.text}"
job_id = resp.json()["job_id"]
print(f"Job: {job_id}")

for attempt in range(60):
    time.sleep(2)
    status_resp = requests.get(f"{BASE}/bulk/status/{job_id}")
    job = status_resp.json()
    print(f"[{attempt*2}s] status={job['status']} processed={job.get('processed',0)}/{job.get('total_rows',job.get('total','?'))}")
    if job["status"] == "completed":
        results = job["results"]
        print(f"\n=== RESULTS ({len(results)} rows) ===")
        for r in results:
            lang = r.get("detected_language", "MISSING")
            method = r.get("translation_method", "MISSING")
            print(f"  Row {r['row_index']}: {r['sentiment']} ({r['confidence']:.1f}%) | lang={lang} | method={method}")
        
        missing_lang = [r for r in results if not r.get("detected_language")]
        missing_method = [r for r in results if not r.get("translation_method")]
        print(f"\nRows missing detected_language: {len(missing_lang)}")
        print(f"Rows missing translation_method: {len(missing_method)}")
        assert len(missing_lang) == 0, "FAIL: detected_language missing from some rows"
        assert len(missing_method) == 0, "FAIL: translation_method missing from some rows"
        print("V3 PASS - all rows have language metadata")
        break
    elif job["status"] == "failed":
        print(f"FAIL: {job.get('error')}")
        break
else:
    print("TIMEOUT - job did not complete in 120 seconds")
