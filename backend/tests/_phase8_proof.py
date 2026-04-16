import requests, json, time, sys
sys.stdout.reconfigure(encoding='utf-8')
base = 'http://localhost:8001'

# Tests 1-3: probe cache hit timing
for i in range(1, 4):
    t = time.time()
    r = requests.get(f'{base}/metrics/translations')
    elapsed = time.time() - t
    reachable = r.json().get('google_reachable')
    print(f'Test {i} (cache hit): {elapsed:.3f}s  google_reachable={reachable}')

# Job count endpoint (H1)
r2 = requests.get(f'{base}/bulk/jobs/count')
print()
print('Job count endpoint:')
print(json.dumps(r2.json(), indent=2))

# V1 regression guard
r3 = requests.get(f'{base}/metrics/translations')
data = r3.json()
print()
print('Translation metrics (post-restart persistence):')
print(json.dumps(data, indent=2))
