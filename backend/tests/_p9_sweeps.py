import requests, json, sys, subprocess, time
sys.stdout.reconfigure(encoding='utf-8')
base = 'http://localhost:8001'

print("=" * 60)
print("SWEEP-7: /metrics/translations")
print("=" * 60)
try:
    r = requests.get(f'{base}/metrics/translations', timeout=10)
    print(json.dumps(r.json(), indent=2))
except Exception as e:
    print(f"ERROR: {e}")

print()
print("=" * 60)
print("SWEEP-8: /bulk/jobs/count")
print("=" * 60)
try:
    r2 = requests.get(f'{base}/bulk/jobs/count', timeout=10)
    print(json.dumps(r2.json(), indent=2))
except Exception as e:
    print(f"ERROR: {e}")

print()
print("=" * 60)
print("SWEEP-12: FastAPI version")
print("=" * 60)
import fastapi
print(f"FastAPI version: {fastapi.__version__}")

print()
print("=" * 60)
print("SWEEP-9: git check-ignore translation_stats.json")
print("=" * 60)
r9 = subprocess.run(
    ['git', 'check-ignore', '-v', 'backend/app/state/translation_stats.json'],
    capture_output=True, text=True, cwd='w:\\ReviewSense-Analytics'
)
print(r9.stdout.strip() or "(no output — NOT ignored)")

print()
print("=" * 60)
print("SWEEP-10: git check-ignore .gitkeep")
print("=" * 60)
r10 = subprocess.run(
    ['git', 'check-ignore', '-v', 'backend/app/state/.gitkeep'],
    capture_output=True, text=True, cwd='w:\\ReviewSense-Analytics'
)
print(r10.stdout.strip() or "(no output — NOT ignored, tracked by git)")

print()
print("=" * 60)
print("SWEEP: state/ directory contents")
print("=" * 60)
import os
state_dir = 'w:\\ReviewSense-Analytics\\backend\\app\\state'
files = os.listdir(state_dir)
for f in files:
    fp = os.path.join(state_dir, f)
    size = os.path.getsize(fp)
    print(f"  {f:40s} {size} bytes")
