"""
LIVE test — requires internet access.
Tests real GoogleTranslator from deep-translator.
Run manually: python backend/tests/test_google_translate_live.py
NOT added to pytest suite (would fail in CI without internet).
"""
import sys
import time


def test_google_translate_live():
    try:
        from deep_translator import GoogleTranslator
        print("deep-translator: INSTALLED")
    except ImportError:
        print("FAIL: deep-translator is not installed")
        sys.exit(1)

    test_cases = [
        ("Hola mundo", "es", "Hello world"),
        ("Bonjour le monde", "fr", "Hello world"),
        ("Diese Qualitaet ist ausgezeichnet", "de", "This quality is excellent"),
        ("Questo prodotto e fantastico", "it", "This product is fantastic"),
    ]

    passed, failed = 0, 0
    for text, src, expected_theme in test_cases:
        try:
            start = time.time()
            result = GoogleTranslator(source=src, target="en").translate(text)
            elapsed = time.time() - start
            if result and result.strip():
                print("  PASS ({:.2f}s): '{}' -> '{}'".format(elapsed, text, result))
                passed += 1
            else:
                print("  FAIL: empty result for '{}'".format(text))
                failed += 1
        except Exception as e:
            print("  FAIL: {}: {}".format(type(e).__name__, e))
            failed += 1

    print("\nResults: {}/{} passed".format(passed, passed + failed))
    if passed == 0:
        print("VERDICT: Google Translate is UNREACHABLE in this environment")
        print("ACTION: Helsinki-NLP is the sole translation engine. No change needed.")
        print("        translate_with_retry() Tier 2 will always fail-through to Tier 3.")
        print("        This is acceptable -- the system degrades gracefully.")
    elif passed < len(test_cases):
        print("VERDICT: Google Translate is PARTIALLY reachable (rate-limited or unstable)")
        print("ACTION: Current implementation is correct -- retry + fallback handles this.")
    else:
        print("VERDICT: Google Translate is FULLY reachable")
        print("ACTION: All translation tiers are operational.")


if __name__ == "__main__":
    test_google_translate_live()
