"""Section 8 — Full validation smoke test with Hinglish."""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from src.pipeline.inference import run_pipeline

tests = [
    # English
    ("This product is amazing, highly recommend it", "EN+", "positive"),
    ("Worst experience ever, do not buy this", "EN-", "negative"),
    # Hindi (Devanagari)
    ("\u092f\u0939 \u092c\u0939\u0941\u0924 \u0905\u091a\u094d\u091b\u093e \u0939\u0948, \u092e\u0941\u091d\u0947 \u092c\u0939\u0941\u0924 \u092a\u0938\u0902\u0926 \u0906\u092f\u093e", "HI+", "positive"),
    ("\u092f\u0939 \u092c\u0939\u0941\u0924 \u0916\u0930\u093e\u092c \u0939\u0948, \u092c\u093f\u0932\u094d\u0915\u0941\u0932 \u092c\u0947\u0915\u093e\u0930", "HI-", "negative"),
    # French
    ("C'est horrible, tres mauvaise qualite", "FR-", "negative"),
    # Arabic
    ("\u0647\u0630\u0627 \u0633\u064a\u0621 \u062c\u062f\u0627", "AR-", "negative"),
    # Japanese
    ("\u3053\u308c\u306f\u7d20\u6674\u3089\u3057\u3044", "JA+", "positive"),
    # Hinglish (Section 3+4 tests)
    ("Yeh product bakwaas hai, paisa barbaad", "HINGL-", "negative"),
    ("Zabardast quality hai, bahut acha product", "HINGL+", "positive"),
    ("Kharab experience, bilkul bekar service", "HINGL-", "negative"),
    ("Mast product hai bhai, ekdum lajawab", "HINGL+", "positive"),
]

print("\n" + "=" * 60)
print("  SECTION 8 — FULL VALIDATION SMOKE TEST")
print("=" * 60 + "\n")

all_pass = True
errors = []
for text, tag, expected_dir in tests:
    r = run_pipeline(text)
    pol = r["polarity"]
    sent = r["sentiment"]
    conf = r["confidence"]
    hinglish = r.get("hinglish_detected", False)

    # Polarity direction check
    if expected_dir == "positive":
        pol_ok = pol > 0
    elif expected_dir == "negative":
        pol_ok = pol < 0
    else:
        pol_ok = pol == 0

    # Sentiment match check
    sent_ok = sent.lower() == expected_dir

    status = "PASS" if (pol_ok and sent_ok) else "FAIL"
    if not (pol_ok and sent_ok):
        all_pass = False
        errors.append({
            "tag": tag, "text": text[:50], "expected": expected_dir,
            "got_sentiment": sent, "got_polarity": pol,
            "pol_ok": pol_ok, "sent_ok": sent_ok,
        })

    hinglish_tag = " [HINGL]" if hinglish else ""
    print(f"  [{status}] {tag:7s} | sentiment={sent:8s} conf={conf:.3f} polarity={pol:+.4f}{hinglish_tag}")
    print(f"           | text={text[:55]}")

print(f"\n{'=' * 60}")
print(f"  Result: {'ALL PASS' if all_pass else f'{len(tests) - len(errors)}/{len(tests)} PASSED'}")
if errors:
    print(f"\n  ERRORS ({len(errors)}):")
    for e in errors:
        print(f"    [{e['tag']}] expected={e['expected']}, got={e['got_sentiment']}, polarity={e['got_polarity']}")
print(f"{'=' * 60}\n")

# Polarity non-zero validation
print("  POLARITY VALIDATION:")
for text, tag, expected_dir in tests:
    r = run_pipeline(text)
    pol = r["polarity"]
    sent = r["sentiment"]
    if sent.lower() in ("positive", "negative") and pol == 0.0:
        print(f"    [FAIL] {tag}: polarity is 0.0 for {sent} prediction!")
    else:
        print(f"    [OK]   {tag}: polarity={pol:+.4f} for {sent}")
print()
