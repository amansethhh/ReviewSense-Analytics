import requests, json, sys
sys.stdout.reconfigure(encoding='utf-8')

base = 'http://localhost:8001'
texts = [
    'Excelente producto, muy recomendado',
    'Tres mauvais service',
    'Die Qualitaet ist ausgezeichnet',
    'This is a great product',
    'Questo prodotto e fantastico',
]
for t in texts:
    r = requests.post(f'{base}/language', json={'text': t, 'model': 'best'})
    d = r.json()
    lang = d.get('language_code', '?')
    sent = d.get('sentiment', '?')
    conf = d.get('confidence', 0)
    print(f'  {lang} -> {sent} ({conf:.1f}%)')

print()
r = requests.get(f'{base}/metrics/translations')
print(json.dumps(r.json(), indent=2))
