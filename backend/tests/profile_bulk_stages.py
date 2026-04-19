"""
Performance profiler for ReviewSense bulk pipeline.
Measures per-stage timing for 10 sample reviews across multiple languages.
Run: python backend/tests/profile_bulk_stages.py
"""
import sys
import os
import time
import logging

# Ensure project root is on sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'src'))

logging.basicConfig(level=logging.WARNING)

# Sample reviews across 10 languages
SAMPLE_REVIEWS = [
    ("This product is absolutely amazing, best purchase ever!", "en"),
    ("Este producto es terrible, no funciona para nada.", "es"),
    ("Ce produit est excellent, je le recommande vivement!", "fr"),
    ("Das Produkt ist nutzlos. Sehr enttäuschend.", "de"),
    ("यह उत्पाद बहुत अच्छा है, मुझे बहुत पसंद आया।", "hi"),
    ("这个产品质量很差，完全不值得购买。", "zh-cn"),
    ("이 제품은 정말 훌륭합니다. 강력히 추천합니다!", "ko"),
    ("Этот продукт ужасен. Полная трата денег.", "ru"),
    ("この製品は素晴らしいです。とても満足しています。", "ja"),
    ("Produto péssimo, não recomendo a ninguém.", "pt"),
]


def profile_stage(label, fn, *args, **kwargs):
    """Run a function and return (result, elapsed_ms)."""
    t0 = time.perf_counter()
    result = fn(*args, **kwargs)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    return result, elapsed_ms


def main():
    print("=" * 70)
    print("  ReviewSense Bulk Pipeline — Per-Stage Profiler")
    print("=" * 70)

    # Import pipeline components
    from backend.app.routes.language import (
        detect_language_adaptive,
        _translate_with_fallback,
    )
    from src.predict import predict_sentiment

    # Warm up models first (exclude from timing)
    print("\n[WARMUP] Loading models...")
    t_warmup = time.perf_counter()
    predict_sentiment("warmup text for model loading")
    try:
        from src.models.aspect import analyze_aspects
        analyze_aspects("warmup text")
    except Exception:
        pass
    try:
        from src.sarcasm_detector import detect_sarcasm
        detect_sarcasm("warmup text for sarcasm")
    except Exception:
        pass
    warmup_ms = (time.perf_counter() - t_warmup) * 1000
    print(f"[WARMUP] Complete in {warmup_ms:.0f}ms\n")

    # Profile each review
    totals = {
        "language_detect": 0.0,
        "translation": 0.0,
        "sentiment_predict": 0.0,
        "absa": 0.0,
        "sarcasm": 0.0,
    }
    review_totals = []

    for idx, (text, expected_lang) in enumerate(SAMPLE_REVIEWS):
        print(f"--- Review {idx+1}/10 ({expected_lang}) ---")
        review_start = time.perf_counter()

        # Stage 1: Language detection
        (lang_code, lang_conf), t_detect = profile_stage(
            "language_detect", detect_language_adaptive, text
        )
        totals["language_detect"] += t_detect
        print(f"  [PERF] language_detect: {t_detect:.1f}ms (detected: {lang_code})")

        # Stage 2: Translation
        if lang_code != "en" or lang_conf < 0.85:
            src_lang = lang_code if lang_code != "unknown" else "auto"
            trans_result, t_translate = profile_stage(
                "translation", _translate_with_fallback, text, src_lang
            )
            english_text = trans_result.get("translated_text") or text
            totals["translation"] += t_translate
            print(f"  [PERF] translation: {t_translate:.1f}ms (method: {trans_result.get('method', 'N/A')})")
        else:
            english_text = text
            t_translate = 0.0
            print(f"  [PERF] translation: SKIPPED (English detected)")

        # Stage 3: Sentiment prediction
        pred_result, t_predict = profile_stage(
            "sentiment_predict", predict_sentiment, english_text
        )
        totals["sentiment_predict"] += t_predict
        sentiment = pred_result.get("label_name", "?")
        confidence = pred_result.get("confidence", 0)
        print(f"  [PERF] sentiment_predict: {t_predict:.1f}ms ({sentiment}, conf={confidence:.3f})")

        # Stage 4: ABSA
        try:
            from src.models.aspect import analyze_aspects
            _, t_absa = profile_stage("absa", analyze_aspects, english_text)
        except Exception:
            t_absa = 0.0
        totals["absa"] += t_absa
        print(f"  [PERF] absa: {t_absa:.1f}ms")

        # Stage 5: Sarcasm
        try:
            from src.sarcasm_detector import detect_sarcasm
            _, t_sarcasm = profile_stage("sarcasm", detect_sarcasm, english_text)
        except Exception:
            t_sarcasm = 0.0
        totals["sarcasm"] += t_sarcasm
        print(f"  [PERF] sarcasm: {t_sarcasm:.1f}ms")

        review_total = (time.perf_counter() - review_start) * 1000
        review_totals.append(review_total)
        print(f"  [PERF] TOTAL per review: {review_total:.1f}ms\n")

    # Summary
    print("=" * 70)
    print("  SUMMARY (10 reviews)")
    print("=" * 70)
    grand_total = sum(review_totals)
    avg_per_review = grand_total / len(review_totals)

    for stage, total_ms in totals.items():
        pct = (total_ms / grand_total) * 100 if grand_total > 0 else 0
        avg = total_ms / len(SAMPLE_REVIEWS)
        print(f"  {stage:20s}: {total_ms:8.1f}ms total | {avg:7.1f}ms avg | {pct:5.1f}% of pipeline")

    print(f"\n  {'GRAND TOTAL':20s}: {grand_total:8.1f}ms")
    print(f"  {'AVG PER REVIEW':20s}: {avg_per_review:8.1f}ms")
    print(f"  {'ESTIMATED 200 REVIEWS':20s}: {avg_per_review * 200 / 1000:8.1f}s")
    print()

    # Identify bottlenecks (>10% of total)
    print("  BOTTLENECKS (>10% of total):")
    for stage, total_ms in sorted(totals.items(), key=lambda x: -x[1]):
        pct = (total_ms / grand_total) * 100 if grand_total > 0 else 0
        if pct > 10:
            print(f"    ⚠ {stage}: {pct:.1f}% — OPTIMIZE THIS")
    print()


if __name__ == "__main__":
    main()
