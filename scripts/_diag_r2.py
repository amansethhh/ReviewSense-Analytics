"""
Diagnostic: R2 pipeline validation with actual unicode strings
"""
import sys
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
from src.pipeline.inference import run_pipeline

cases = [
    ("\u0c2f\u0c3e, \u0c2c\u0c3e\u0c17\u0c41\u0c02\u0c26\u0c3f",  "Negative"),   # Telugu: "Yes, it is good" - control test
    ("terrible product, do not buy",           "Negative"),  # clear English negative
    ("C\u2019est incroyable",                  "Positive"),  # French positive (unicode apostrophe)
    ("Das ist schrecklich",                    "Negative"),  # German negative
    ("I love this product",                    "Positive"),  # English positive
    ("This product is okay",                   "Neutral"),   # English neutral
    ("Excellent quality, highly recommend",    "Positive"),  # English strong positive
    ("Very bad, waste of money",               "Negative"),  # English strong negative
]

print("\n=== V5 Pipeline Test ===\n")
for text, expected in cases:
    r = run_pipeline(text)
    got  = str(r.get("label_name", r.get("label", ""))).capitalize()
    conf = r.get("confidence", 0.0)
    lang = r.get("language_detected", "?")
    ok   = "PASS" if got == expected else "FAIL"
    print(f"{ok} [{expected}->{got}] conf={conf:.3f} lang={lang} | {text[:40]}")
