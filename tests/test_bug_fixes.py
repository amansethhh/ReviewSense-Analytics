"""
E2E Test Suite — BUG #2-6 Verification.

Tests for:
  - BUG #2: Language Detection (CJK confusion, Portuguese/French)
  - BUG #3: Neutral Over-Classification
  - BUG #4: ABSA Enhancement
  - BUG #5: Batch Inference Performance
  - BUG #6: Frontend (CSS only, no runtime test)
"""

import sys
from pathlib import Path

# Ensure project root on path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Also add backend/ for app.utils imports
BACKEND_ROOT = PROJECT_ROOT / "backend"
if str(BACKEND_ROOT) not in sys.path:
    sys.path.insert(0, str(BACKEND_ROOT))

import logging
logging.basicConfig(level=logging.WARNING)


def main():
    print("\n" + "=" * 70)
    print("  REVIEWSENSE ANALYTICS -- BUG #2-6 FIX VERIFICATION")
    print("=" * 70)

    results = []

    # ================================================
    # BUG #2: CJK Language Detection
    # ================================================
    print("\n--- BUG #2: CJK Language Detection ---")
    try:
        from app.utils.language_detection import (
            detect_script_unicode,
            detect_language_robust,
            detect_hinglish,
        )

        cjk_tests = [
            # (text, expected_lang, description)
            (
                "zuihaodemaiwuleshizhilianghaojimanzu",  # pinyin
                None,  # No CJK characters
                "Pinyin (no CJK chars) -> None"
            ),
            (
                "zuigao no kaimono deshita!",
                None,  # No CJK characters  
                "Romaji Japanese -> None"
            ),
        ]

        # Script detection tests
        script_tests = [
            ("privet mir", None, "Cyrillic transliterated -> None"),
            ("marhaba bialealim", None, "Arabic transliterated -> None"),
        ]

        # These test detect_script_unicode directly
        unicode_tests = [
            ("\u6700\u9ad8\u306e\u8cb7\u3044\u7269\u3067\u3057\u305f", "ja",
             "Japanese with Hiragana -> ja"),
            ("\u4f60\u597d\u4e16\u754c", "zh-cn",
             "Chinese only CJK -> zh-cn"),
            ("\ud55c\uad6d\uc5b4 \ud14d\uc2a4\ud2b8", "ko",
             "Korean Hangul -> ko"),
            ("\u0645\u0631\u062d\u0628\u0627 \u0628\u0627\u0644\u0639\u0627\u0644\u0645", "ar",
             "Arabic script -> ar"),
            ("\u041f\u0440\u0438\u0432\u0435\u0442 \u043c\u0438\u0440", "ru",
             "Cyrillic -> ru"),
            ("\u0e2a\u0e27\u0e31\u0e2a\u0e14\u0e35\u0e04\u0e23\u0e31\u0e1a", "th",
             "Thai script -> th"),
        ]

        all_pass = True
        for text, expected, desc in unicode_tests:
            actual = detect_script_unicode(text)
            ok = actual == expected
            if not ok:
                all_pass = False
            print(f"  {'PASS' if ok else 'FAIL'}  {desc}: got={actual}")

        results.append(("BUG-2: Unicode script detection", all_pass))

        # Critical test: Japanese vs Chinese
        jp_text = "\u6700\u9ad8\u306e\u8cb7\u3044\u7269\u3067\u3057\u305f\uff01\u54c1\u8cea\u304c\u7d20\u6674\u3089\u3057\u304f\u3068\u3066\u3082\u6e80\u8db3\u3057\u3066\u3044\u307e\u3059\u3002"
        jp_result = detect_language_robust(jp_text)
        ok_jp = jp_result["language"] == "ja"
        print(f"  {'PASS' if ok_jp else 'FAIL'}  Japanese full sentence -> "
              f"{jp_result['language']} (method={jp_result['method']})")
        results.append(("BUG-2: Japanese not Chinese", ok_jp))

        cn_text = "\u8fd9\u4e2a\u4ea7\u54c1\u975e\u5e38\u597d"
        cn_result = detect_language_robust(cn_text)
        ok_cn = cn_result["language"] == "zh-cn"
        print(f"  {'PASS' if ok_cn else 'FAIL'}  Chinese -> "
              f"{cn_result['language']} (method={cn_result['method']})")
        results.append(("BUG-2: Chinese detected correctly", ok_cn))

    except Exception as e:
        print(f"  FAIL  BUG-2 import error: {e}")
        results.append(("BUG-2: Language Detection", False))

    # Hinglish detection
    try:
        ok_h1 = detect_hinglish("Bahut accha product hai yaar")
        ok_h2 = not detect_hinglish("This is a great product")
        print(f"  {'PASS' if ok_h1 else 'FAIL'}  Hinglish detected: "
              f"'Bahut accha...' = {ok_h1}")
        print(f"  {'PASS' if ok_h2 else 'FAIL'}  English not Hinglish: "
              f"'This is...' = {not ok_h2}")
        results.append(("BUG-2: Hinglish detection", ok_h1 and ok_h2))
    except Exception as e:
        print(f"  FAIL  Hinglish test: {e}")
        results.append(("BUG-2: Hinglish detection", False))

    # ================================================
    # BUG #3: Neutral Over-Classification
    # ================================================
    print("\n--- BUG #3: Neutral Over-Classification ---")
    try:
        from src.predict import predict_sentiment

        sentiment_tests = [
            ("This is the best product I have ever bought! Amazing quality!",
             "Positive", "Clear positive"),
            ("This product is terrible. Complete waste of money.",
             "Negative", "Clear negative"),
            ("Excellent quality! Works perfectly and looks great.",
             "Positive", "Strong positive"),
            ("Worst purchase ever. Broke within a day.",
             "Negative", "Strong negative"),
            ("Absolutely love this! Highly recommended.",
             "Positive", "Enthusiastic positive"),
        ]

        neutral_count = 0
        total = len(sentiment_tests)
        for text, expected, desc in sentiment_tests:
            result = predict_sentiment(text)
            actual = result["label_name"]
            ok = actual == expected
            if actual == "Neutral":
                neutral_count += 1
            print(f"  {'PASS' if ok else 'FAIL'}  {desc}: "
                  f"expected={expected}, got={actual} "
                  f"(conf={result['confidence']:.3f})")

        # BUG #3 FIX: neutral should NOT be >50% of clear sentiments
        neutral_pct = neutral_count / total * 100
        ok_dist = neutral_count <= total * 0.5
        print(f"\n  Neutral rate: {neutral_count}/{total} ({neutral_pct:.0f}%)")
        print(f"  {'PASS' if ok_dist else 'FAIL'}  Neutral <50% check")
        results.append(("BUG-3: Sentiment distribution", ok_dist))

    except Exception as e:
        print(f"  FAIL  BUG-3 error: {e}")
        results.append(("BUG-3: Sentiment distribution", False))

    # ================================================
    # BUG #4: ABSA Enhancement
    # ================================================
    print("\n--- BUG #4: ABSA Enhancement ---")
    try:
        from backend.app.utils.absa import (
            extract_aspects_enhanced,
            analyze_aspect_sentiment,
            perform_absa,
        )

        # Test aspect extraction
        text1 = "The product quality is excellent but the price is too high."
        aspects1 = extract_aspects_enhanced(text1)
        ok_a1 = len(aspects1) >= 2
        print(f"  {'PASS' if ok_a1 else 'FAIL'}  "
              f"Aspect extraction: {aspects1} (>= 2 expected)")

        # Test ABSA pipeline
        text2 = "Great design and fast performance but terrible customer service."
        absa_result = perform_absa(text2)
        ok_a2 = absa_result["aspect_count"] >= 2
        ok_a3 = len(absa_result["aspects"]) >= 1
        print(f"  {'PASS' if ok_a2 else 'FAIL'}  "
              f"ABSA aspects found: {absa_result['aspect_count']}")
        print(f"  {'PASS' if ok_a3 else 'FAIL'}  "
              f"ABSA has results: {len(absa_result['aspects'])} aspects")
        print(f"  Overall: {absa_result['overall_sentiment']} "
              f"(polarity={absa_result['total_polarity']:.3f})")

        # Test polarity-based aggregation
        text3 = "Terrible quality. Waste of money. Would not recommend."
        absa_neg = perform_absa(text3)
        ok_a4 = absa_neg["overall_sentiment"] == "negative"
        print(f"  {'PASS' if ok_a4 else 'FAIL'}  "
              f"Negative ABSA: {absa_neg['overall_sentiment']} "
              f"(polarity={absa_neg['total_polarity']:.3f})")

        results.append(("BUG-4: ABSA extraction", ok_a1 and ok_a2))
        results.append(("BUG-4: ABSA polarity aggregation", ok_a4))

    except Exception as e:
        print(f"  FAIL  BUG-4 error: {e}")
        results.append(("BUG-4: ABSA", False))

    # ================================================
    # BUG #5: Batch Inference
    # ================================================
    print("\n--- BUG #5: Batch Inference ---")
    try:
        from src.models.sentiment import predict_batch
        import time

        test_texts = [
            "Great product!",
            "Terrible quality.",
            "It's okay.",
            "Best purchase ever!",
            "Complete waste of money.",
        ] * 10  # 50 texts

        start = time.time()
        batch_results = predict_batch(test_texts, batch_size=32)
        elapsed = time.time() - start

        ok_b1 = len(batch_results) == len(test_texts)
        ok_b2 = elapsed < 10.0  # Should be well under 10s for 50 texts

        labels = [r["label_name"] for r in batch_results]
        pos = labels.count("Positive")
        neg = labels.count("Negative")
        neu = labels.count("Neutral")

        print(f"  {'PASS' if ok_b1 else 'FAIL'}  "
              f"Batch returned {len(batch_results)}/{len(test_texts)} results")
        print(f"  {'PASS' if ok_b2 else 'FAIL'}  "
              f"Batch time: {elapsed:.2f}s ({elapsed/len(test_texts)*1000:.0f}ms/review)")
        print(f"  Distribution: {pos} pos, {neg} neg, {neu} neutral")

        # Verify no 85% neutral collapse
        ok_b3 = neu / len(test_texts) < 0.70
        print(f"  {'PASS' if ok_b3 else 'FAIL'}  "
              f"Neutral rate: {neu/len(test_texts)*100:.0f}% (<70%)")

        results.append(("BUG-5: Batch inference works", ok_b1))
        results.append(("BUG-5: Batch performance", ok_b2))
        results.append(("BUG-5: Batch distribution", ok_b3))

    except Exception as e:
        print(f"  FAIL  BUG-5 error: {e}")
        results.append(("BUG-5: Batch Inference", False))

    # ================================================
    # BUG #6: Frontend CSS Validation
    # ================================================
    print("\n--- BUG #6: Frontend CSS/Config ---")
    try:
        css_path = PROJECT_ROOT / "frontend" / "src" / "styles" / "animations.css"
        css_content = css_path.read_text(encoding="utf-8")

        ok_c1 = "prefers-reduced-motion" in css_content
        ok_c2 = "translateZ(0)" in css_content
        ok_c3 = "backface-visibility: hidden" in css_content
        ok_c4 = ".animated-card" in css_content

        main_tsx = (PROJECT_ROOT / "frontend" / "src" / "main.tsx").read_text()
        ok_c5 = "import.meta.env.DEV" in main_tsx

        vite_config = (PROJECT_ROOT / "frontend" / "vite.config.ts").read_text()
        ok_c6 = "cssCodeSplit: false" in vite_config

        print(f"  {'PASS' if ok_c1 else 'FAIL'}  prefers-reduced-motion")
        print(f"  {'PASS' if ok_c2 else 'FAIL'}  GPU compositing (translateZ)")
        print(f"  {'PASS' if ok_c3 else 'FAIL'}  backface-visibility")
        print(f"  {'PASS' if ok_c4 else 'FAIL'}  .animated-card class")
        print(f"  {'PASS' if ok_c5 else 'FAIL'}  StrictMode dev-only")
        print(f"  {'PASS' if ok_c6 else 'FAIL'}  CSS code-split disabled")

        results.append(("BUG-6: Animation CSS", all([ok_c1, ok_c2, ok_c3, ok_c4])))
        results.append(("BUG-6: Build config", ok_c5 and ok_c6))

    except Exception as e:
        print(f"  FAIL  BUG-6 error: {e}")
        results.append(("BUG-6: Frontend CSS", False))

    # ================================================
    # New component validation
    # ================================================
    print("\n--- Section 3: TranslationStatus Component ---")
    try:
        tsx_path = (
            PROJECT_ROOT / "frontend" / "src" / "components" / "ui"
            / "TranslationStatus.tsx"
        )
        ok_tsx = tsx_path.exists()
        print(f"  {'PASS' if ok_tsx else 'FAIL'}  TranslationStatus.tsx exists")
        results.append(("Section 3: TranslationStatus", ok_tsx))
    except Exception as e:
        print(f"  FAIL  {e}")
        results.append(("Section 3: TranslationStatus", False))

    # ================================================
    # SUMMARY
    # ================================================
    print("\n" + "=" * 70)
    print("  SUMMARY")
    print("=" * 70)
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    for name, ok in results:
        print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    print(f"\n  Result: {passed}/{total} tests passed")
    if passed == total:
        print("  ALL TESTS PASSED!")
    else:
        print(f"  {total - passed} test(s) need attention")
    print("=" * 70 + "\n")

    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
