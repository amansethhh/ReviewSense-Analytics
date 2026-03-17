"""Unified inference pipeline for ReviewSense Analytics.

Single entry point for all analysis: language detection → translation →
sentiment → sarcasm (optional) → aspect analysis.

Every input follows the SAME pipeline. Non-English text is ALWAYS
translated before running the sentiment model.
"""

from __future__ import annotations


def run_pipeline(
    text: str,
    enable_sarcasm: bool = False,
    enable_aspects: bool = True,
) -> dict:
    """Run the full NLP pipeline on a single text input.

    Args:
        text: Raw review text in any language.
        enable_sarcasm: Whether to run sarcasm/irony detection.
        enable_aspects: Whether to run aspect-based analysis.

    Returns:
        dict with keys: original, language, language_name, flag_emoji,
        translated, was_translated, sentiment, label, confidence, scores,
        polarity, subjectivity, sarcasm (optional), aspects (optional).
    """
    from src.models.language import detect_language
    from src.models.translation import translate_to_english
    from src.models.sentiment import predict as sentiment_predict

    original = str(text or "").strip()
    if not original:
        return _empty_result()

    # Step 1: Detect language
    lang_info = detect_language(original)
    lang_code = lang_info["code"]

    # Step 2: Translate if not English
    if lang_code not in ("en", "unknown"):
        translated = translate_to_english(original, src_lang=lang_code)
        was_translated = translated.strip().lower() != original.strip().lower()
    else:
        translated = original
        was_translated = False

    # Step 3: Run sentiment on ENGLISH text only
    analysis_text = translated if was_translated else original
    print(f"[ReviewSense] INPUT TO MODEL: {analysis_text[:200]}")  # Debug log

    sentiment = sentiment_predict(analysis_text)

    # Confidence calibration
    confidence = sentiment["confidence"]
    label_name = sentiment["label_name"]
    if confidence < 0.6:
        label_name = "Uncertain"

    # Compute polarity from scores: positive_prob - negative_prob
    scores = sentiment["scores"]  # [neg, neu, pos]
    polarity = scores[2] - scores[0]
    subjectivity = 1.0 - scores[1]  # higher when not neutral

    # Step 4: Sarcasm (optional)
    sarcasm_result = None
    if enable_sarcasm:
        from src.models.sarcasm_model import predict as sarcasm_predict
        sarcasm_result = sarcasm_predict(analysis_text)

    # Step 5: Aspect analysis (optional)
    aspects = []
    if enable_aspects:
        try:
            from src.models.aspect import analyze_aspects
            aspects = analyze_aspects(analysis_text)
        except Exception as e:
            print(f"[ReviewSense] Aspect analysis error: {e}")
            aspects = []

    return {
        "original": original,
        "language": lang_code,
        "language_name": lang_info["name"],
        "flag_emoji": lang_info["flag_emoji"],
        "translated": translated,
        "was_translated": was_translated,
        "sentiment": label_name,
        "label": sentiment["label"],
        "confidence": confidence,
        "scores": scores,
        "polarity": round(polarity, 4),
        "subjectivity": round(subjectivity, 4),
        "sarcasm": sarcasm_result,
        "sarcasm_status": "ENABLED" if enable_sarcasm else "DISABLED",
        "aspects": aspects,
    }


def run_pipeline_batch(
    texts: list[str],
    enable_sarcasm: bool = False,
    enable_aspects: bool = False,
) -> list[dict]:
    """Batch pipeline — uses vectorized sentiment inference.

    Translation and language detection are still per-row since
    each row may be a different language.
    """
    from src.models.language import detect_language
    from src.models.translation import translate_to_english
    from src.models.sentiment import predict_batch

    if not texts:
        return []

    clean_texts = [str(t or "").strip() for t in texts]

    # Step 1+2: Detect language + translate per row
    translated_texts = []
    lang_infos = []
    for text in clean_texts:
        if not text:
            translated_texts.append("")
            lang_infos.append({"code": "unknown", "name": "Unknown", "flag_emoji": "🏳️", "was_translated": False})
            continue

        lang = detect_language(text)
        if lang["code"] not in ("en", "unknown"):
            tr = translate_to_english(text, src_lang=lang["code"])
            was_tr = tr.strip().lower() != text.strip().lower()
        else:
            tr = text
            was_tr = False

        translated_texts.append(tr if was_tr else text)
        lang_infos.append({**lang, "was_translated": was_tr, "translated": tr})

    # Step 3: Batch sentiment on all translated texts
    print(f"[ReviewSense] BATCH: {len(translated_texts)} texts for sentiment model")
    sentiments = predict_batch(translated_texts)

    # Step 4+5: Per-row sarcasm + aspects (optional)
    results = []
    for i, (text, sent_result) in enumerate(zip(clean_texts, sentiments)):
        scores = sent_result["scores"]
        confidence = sent_result["confidence"]
        label_name = sent_result["label_name"]
        if confidence < 0.6:
            label_name = "Uncertain"

        polarity = scores[2] - scores[0]
        subjectivity = 1.0 - scores[1]
        li = lang_infos[i]
        analysis_text = translated_texts[i]

        sarcasm_result = None
        if enable_sarcasm:
            try:
                from src.models.sarcasm_model import predict as sarcasm_predict
                sarcasm_result = sarcasm_predict(analysis_text)
            except Exception:
                sarcasm_result = {"is_sarcastic": False, "confidence": 0.0, "reason": "Error"}

        aspect_list = []
        if enable_aspects:
            try:
                from src.models.aspect import analyze_aspects
                aspect_list = analyze_aspects(analysis_text)
            except Exception:
                aspect_list = []

        results.append({
            "original": text,
            "language": li.get("code", "unknown"),
            "language_name": li.get("name", "Unknown"),
            "flag_emoji": li.get("flag_emoji", "🏳️"),
            "translated": li.get("translated", text),
            "was_translated": li.get("was_translated", False),
            "sentiment": label_name,
            "label": sent_result["label"],
            "label_name": sent_result["label_name"],
            "confidence": confidence,
            "scores": scores,
            "polarity": round(polarity, 4),
            "subjectivity": round(subjectivity, 4),
            "sarcasm": sarcasm_result,
            "sarcasm_status": "ENABLED" if enable_sarcasm else "DISABLED",
            "aspects": aspect_list,
        })

    return results


def _empty_result() -> dict:
    return {
        "original": "",
        "language": "unknown",
        "language_name": "Unknown",
        "flag_emoji": "🏳️",
        "translated": "",
        "was_translated": False,
        "sentiment": "Neutral",
        "label": 1,
        "confidence": 0.0,
        "scores": [0.0, 1.0, 0.0],
        "polarity": 0.0,
        "subjectivity": 0.0,
        "sarcasm": None,
        "sarcasm_status": "DISABLED",
        "aspects": [],
    }
