import sys
sys.path.insert(0, '.')

print('=== End-to-end pipeline smoke test ===')
from src.pipeline.inference import run_pipeline

tests = [
    ('ZH NEG', '\u8fd9\u4e2a\u4ea7\u54c1\u592a\u5dee\u4e86\uff0c\u6839\u672c\u4e0d\u503c\u8fd9\u4e2a\u4ef7\u683c\uff0c\u8d28\u91cf\u4ee4\u4eba\u5931\u671b\u3002'),
    ('ZH POS', '\u975e\u5e38\u597d\u7684\u4ea7\u54c1\uff01\u7269\u8d85\u6240\u503c\uff0c\u8d28\u91cf\u8d85\u51fa\u9884\u671f\uff0c\u975e\u5e38\u6ee1\u610f\uff01'),
    ('AR POS', '\u0645\u0646\u062a\u062c \u0631\u0627\u0626\u0639 \u062c\u062f\u0627\u060c \u0623\u0646\u0635\u062d \u0628\u0627\u0644\u0634\u0631\u0627\u0621'),
    ('HI NEG', '\u092f\u0647 \u0909\u0924\u094d\u092a\u093e\u0926 \u092c\u0939\u0941\u0924 \u0916\u0930\u093e\u092c \u0939\u0948'),
    ('EN POS', 'This product is absolutely amazing, best purchase ever!'),
    ('EN NEG', 'Terrible product, waste of money, broke after one day.'),
]

import time
for label, text in tests:
    t0 = time.time()
    r = run_pipeline(text)
    elapsed = time.time() - t0
    translated = r.get('translated', '')[:50]
    print(f"[{label}] ({elapsed:.2f}s) lang={r['language']} was_translated={r['was_translated']}")
    print(f"         sentiment={r['sentiment']} conf={r['confidence']:.3f} pol={r['polarity']:.3f} nc={r['neutral_corrected']}")
    if r['was_translated']:
        print(f"         translation: {translated}")
    print()
