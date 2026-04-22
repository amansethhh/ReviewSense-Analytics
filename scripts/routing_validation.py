"""Section 6: Routing validation — verify all routes match expected."""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from src.pipeline.inference import run_pipeline

# Section 6 routing correctness check
routing_tests = [
    ("This is great", "ENGLISH", "roberta"),
    ("Yeh bakwaas hai", "HINGLISH", "roberta"),
    ("C'est terrible", "MULTILINGUAL", "xlm-r"),
    ("\u3053\u308c\u306f\u7d20\u6674\u3089\u3057\u3044", "MULTILINGUAL", "roberta"),  # Japanese: valid translation → RoBERTa
    ("\u0647\u0630\u0627 \u0633\u064a\u0621 \u062c\u062f\u0627", "MULTILINGUAL", "roberta"),  # Arabic: valid translation → RoBERTa
    ("Sehr schlecht", "MULTILINGUAL", "xlm-r"),  # German: XLM-R preferred
    ("Das ist fantastisch", "MULTILINGUAL", "xlm-r"),  # German: XLM-R preferred
]

print("\n" + "=" * 70)
print("  SECTION 6 — ROUTING VALIDATION")
print("=" * 70)

all_pass = True
for text, expected_route, expected_model in routing_tests:
    r = run_pipeline(text)
    trace = r.get("pipeline_trace", {})
    actual_route = trace.get("route", "?")
    actual_model = trace.get("model_used", "?")
    
    route_ok = actual_route == expected_route
    model_ok = actual_model == expected_model
    status = "PASS" if (route_ok and model_ok) else "FAIL"
    if not (route_ok and model_ok):
        all_pass = False

    print(f"  [{status}] {text:30s}")
    print(f"         route: {actual_route:15s} (expected: {expected_route})")
    print(f"         model: {actual_model:15s} (expected: {expected_model})")
    print(f"         sentiment: {r['sentiment']} ({r['confidence']:.3f})")
    print()

print(f"{'=' * 70}")
print(f"  Result: {'ALL PASS' if all_pass else 'FAIL'}")
print(f"{'=' * 70}\n")

# Translation safety check
print("  TRANSLATION SAFETY CHECK:")
safety_tests = [
    "\u8fd9\u4e2a\u4ea7\u54c1\u5f88\u597d",  # Chinese
    "\u3053\u308c\u306f\u3072\u3069\u3044",  # Japanese
    "\u0647\u0630\u0627 \u0633\u064a\u0621 \u062c\u062f\u0627",  # Arabic
]
for text in safety_tests:
    r = run_pipeline(text)
    translated = r.get("translated", "")
    has_brackets = "[" in translated
    trace = r.get("pipeline_trace", {})
    print(f"    {text:20s} -> {translated[:50]:50s} brackets={'YES' if has_brackets else 'NO'} valid={trace.get('translation_valid')}")
print()
