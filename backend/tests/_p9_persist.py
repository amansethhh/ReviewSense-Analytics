import requests, json, sys
sys.stdout.reconfigure(encoding='utf-8')
base = 'http://localhost:8001'

# Trigger 3 translations through /language
texts = [
    'Excelente producto, muy recomendado',
    'Tres mauvais service, vraiment horrible',
    'This is a great product',
]
for t in texts:
    r = requests.post(f'{base}/language', json={'text': t, 'model': 'best'}, timeout=15)
    d = r.json()
    print(f"  {d.get('language_code','?')} -> {d.get('sentiment')} ({d.get('confidence',0):.1f}%)")

print()
print("Metrics after 3 /language calls:")
r2 = requests.get(f'{base}/metrics/translations', timeout=10)
data = r2.json()
print(json.dumps(data, indent=2))

import os
stats_path = 'w:\\ReviewSense-Analytics\\backend\\app\\state\\translation_stats.json'
print(f"\nState file size: {os.path.getsize(stats_path)} bytes")
with open(stats_path) as f:
    print("State file contents:")
    print(f.read())
