"""Prediction helpers for ReviewSense Analytics.

Post-inference pipeline layers:
  1. Short-text negation guard   (ADD-ON 1)
  2. Neutral correction v2       (VADER-primary, TextBlob secondary)
  3. Confidence calibration      (Problem 5)
  4. Temperature scaling         (ADD-ON 5)

All functions operate on LABEL_MAP integers: 0=Negative, 1=Neutral, 2=Positive.
"""

from __future__ import annotations

import logging
import math

from src.config import LABEL_MAP

logger = logging.getLogger("reviewsense")

# ═══════════════════════════════════════════════════════════════
# VADER — module-level instance (instantaneous, no model loading)
# ═══════════════════════════════════════════════════════════════

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer as VaderAnalyzer
    _vader = VaderAnalyzer()
    _VADER_AVAILABLE = True
except ImportError:
    _vader = None
    _VADER_AVAILABLE = False
    logger.warning("vaderSentiment not installed — VADER corrections disabled")

# Legacy non-Latin grouping retained for compatibility.
# V6 polarity logic is stricter: TextBlob/VADER run only for English.
_NON_LATIN_LANGS = frozenset({
    "ja", "ko", "zh", "zh-cn", "zh-tw", "hi", "ar",
    "ru", "uk", "bg", "el", "th", "he", "ka", "ur", "fa", "bn",
})

# ═══════════════════════════════════════════════════════════════
# CONSTANTS — Neutral correction thresholds (Problem 1)
# ═══════════════════════════════════════════════════════════════

CONFIDENCE_THRESHOLD = 0.72   # below this = model uncertain
POLARITY_LOW  = -0.25         # tightened: reduces neutral overcorrection window
POLARITY_HIGH = +0.25         # tightened: reduces neutral overcorrection window
POLARITY_WEAK = 0.25          # |polarity| below this = genuinely neutral zone

# ═══════════════════════════════════════════════════════════════
# CONSTANTS — Short-text guard terms (ADD-ON 1)
# ═══════════════════════════════════════════════════════════════

EXPLICIT_NEGATIVE_TERMS = [
    "bad", "poor", "terrible", "awful", "horrible", "worst", "dreadful",
    "disappointing", "useless", "broken", "defective", "faulty", "failed",
    "failure", "garbage", "trash", "waste", "scam", "fraud", "worthless",
    "not working", "doesn't work", "does not work", "stopped working",
    "never works", "wouldn't recommend", "would not recommend",
    "do not buy", "don't buy", "avoid", "regret", "regrettable",
    "misleading", "inferior", "substandard", "unacceptable", "disgusting",
]

EXPLICIT_POSITIVE_TERMS = [
    "excellent", "amazing", "fantastic", "wonderful", "outstanding",
    "brilliant", "superb", "perfect", "exceptional", "great", "awesome",
    "impressive", "love", "loved", "best", "highly recommend",
    "would recommend", "five stars", "5 stars", "top quality",
    "worth every", "exceeded expectations", "blown away",
]

# ═══════════════════════════════════════════════════════════════
# CONSTANTS — Temperature scaling (ADD-ON 5)
# ═══════════════════════════════════════════════════════════════

CALIBRATION_TEMPERATURE = 1.8
# T > 1.0 softens softmax distribution.
# 1.8 derived from observed overconfidence pattern across 200 English bulk reviews.

# ═══════════════════════════════════════════════════════════════
# V3: UNCERTAIN label removed — confidence IS the uncertainty signal
# Threshold kept for backward API compatibility only.
# ═══════════════════════════════════════════════════════════════

CONFIDENCE_UNCERTAIN_THRESHOLD = 0.60  # Kept for API compat — never overrides label

# ═══════════════════════════════════════════════════════════════
# SECTION 1 — Entropy-based confidence calibration
# ═══════════════════════════════════════════════════════════════

def compute_calibrated_confidence(probs: list) -> float:
    """Section 1: Compute calibrated confidence using entropy.

    Raw softmax confidence is unreliable — a model can output 0.45
    for all 3 classes and still pick one via argmax.

    Entropy measures true uncertainty:
      - Low entropy = model is sure (one class dominates)
      - High entropy = model is confused (uniform distribution)

    Returns calibrated confidence in [0, 1].
    """
    entropy = -sum(p * math.log(p + 1e-9) for p in probs)
    max_entropy = math.log(len(probs))
    normalized_entropy = entropy / max_entropy
    confidence = 1 - normalized_entropy
    return round(confidence, 4)


# ═══════════════════════════════════════════════════════════════
# SECTION 2 — Margin-based decision layer
# ═══════════════════════════════════════════════════════════════

DECISION_MARGIN_THRESHOLD = 0.06


def apply_decision_layer(probs: list, label_map: dict) -> tuple:
    """Section 2: Margin-based decision for ambiguous predictions.

    Instead of blindly trusting argmax, check the margin between
    the top-2 predictions. If the margin is too small, the model
    is genuinely ambiguous → route to neutral.

    Args:
        probs: [neg, neu, pos] softmax probabilities
        label_map: {0: 'Negative', 1: 'Neutral', 2: 'Positive'}

    Returns:
        (pred_class: int, margin: float, decision_type: str)
    """
    sorted_indices = sorted(range(len(probs)), key=lambda i: probs[i], reverse=True)
    top1 = probs[sorted_indices[0]]
    top2 = probs[sorted_indices[1]]
    margin = top1 - top2

    if margin < DECISION_MARGIN_THRESHOLD:
        logger.info(
            "[DECISION] margin=%.4f < %.2f → neutral (ambiguous)",
            margin, DECISION_MARGIN_THRESHOLD,
        )
        return 1, margin, "ambiguous"

    return sorted_indices[0], margin, "confident"

# ═══════════════════════════════════════════════════════════════
# SECTION 1 — Input routing (hybrid architecture)
# ═══════════════════════════════════════════════════════════════

def route_input(text: str, lang: str) -> str:
    """Section 1: Determine pipeline route for an input.

    Returns:
        "ENGLISH"       — direct RoBERTa inference
        "HINGLISH"      — normalize → RoBERTa inference
        "MULTILINGUAL"  — translate → (valid → RoBERTa, invalid → XLM-R)

    NOTE: Hinglish is checked FIRST because detect_language() returns
    lang_code="en" for Roman-script Hinglish text.
    Also catches non-English Latin-script text misdetected as "en".
    """
    from src.models.language import detect_hinglish
    import re

    # Hinglish check MUST come before English check
    if detect_hinglish(text):
        return "HINGLISH"

    if lang not in ("en", "unknown"):
        return "MULTILINGUAL"

    # Language detector said "en" — but verify it's actually English.
    # Short French/German/Spanish texts often get misclassified as English.
    # Check for diacritical marks (é, ä, ñ, etc.) or common non-English words.
    if lang == "en":
        # Diacritical mark check (not present in English)
        if re.search(r'[àáâãäåæçèéêëìíîïðñòóôõöùúûüýþÿ]', text.lower()):
            return "MULTILINGUAL"

        # Common non-English word check (short high-frequency words)
        _NON_ENGLISH_MARKERS = frozenset({
            # German
            "sehr", "schlecht", "ich", "bin", "ist", "nicht", "das", "gut",
            "fantastisch", "schrecklich", "furchtbar",
            # French
            "c'est", "tres", "très", "je", "une", "est", "pas", "rien",
            "mauvais", "mauvaise", "moyen", "produit",
            # Spanish
            "muy", "bueno", "malo", "esto", "esta", "pero", "mejor", "peor",
            # Italian
            "molto", "questo", "questa", "buono", "cattivo",
            # Portuguese
            "muito", "bom", "mau", "este", "esta",
        })
        tokens = set(text.lower().replace("'", " ").split())
        if tokens & _NON_ENGLISH_MARKERS:
            return "MULTILINGUAL"

    return "ENGLISH"


# ═══════════════════════════════════════════════════════════════
# STEP 0 — Input safety guard
# ═══════════════════════════════════════════════════════════════

def _input_safety_guard(text):
    """Early exit for empty or near-empty inputs.

    Returns a safe result dict if input is invalid, None otherwise.
    """
    if not text or not str(text).strip() or len(str(text).strip()) < 2:
        return {
            "label": 1,
            "label_name": "Neutral",
            "confidence": 0.0,
            "raw_confidence": 0.0,
            "polarity": 0.0,
            "subjectivity": 0.0,
            "neutral_corrected": False,
            "correction_reason": "",
            "guard_applied": None,
            "temperature_scaled": False,
            "translation_status": "OK",
            "translation_flagged": False,
            "hinglish_detected": False,
            "analysis_input_source": "original",
            "sarcasm_detected": False,
            "sarcasm_confidence": 0.0,
            "sarcasm_applied": False,
            "sarcasm_reason": "",
            "translation_failed": False,
            "model_used": "roberta",
            "error": "Empty or invalid input",
        }
    return None


# ═══════════════════════════════════════════════════════════════
# STEP 5 — Short-text negation guard (ADD-ON 1)
# ═══════════════════════════════════════════════════════════════

def apply_short_text_guard(text: str,
                            pred_class: int,
                            confidence: float) -> dict:
    """Guard for short declarative sentences where RoBERTa fails.

    Only fires on texts of 12 words or fewer.
    Uses LABEL_MAP integers: 0=Negative, 1=Neutral, 2=Positive.
    """
    word_count = len(text.split())
    if word_count > 12:
        return {"pred_class": pred_class,
                "confidence": confidence,
                "guard_applied": None}

    text_lower = text.lower()
    has_negative = any(t in text_lower for t in EXPLICIT_NEGATIVE_TERMS)
    has_positive = any(t in text_lower for t in EXPLICIT_POSITIVE_TERMS)

    # Predicted Positive (2) but text contains explicit negative terms
    if has_negative and pred_class == 2 and confidence < 0.90:
        return {"pred_class": 0,
                "confidence": round(1 - confidence, 4),
                "guard_applied": "short_text_negation"}

    # Predicted Negative (0) but text contains explicit positive terms
    if has_positive and pred_class == 0 and confidence < 0.90:
        return {"pred_class": 2,
                "confidence": round(1 - confidence, 4),
                "guard_applied": "short_text_positive"}

    return {"pred_class": pred_class,
            "confidence": confidence,
            "guard_applied": None}


# ═══════════════════════════════════════════════════════════════
# STEP 6 — Neutral correction (Problem 1 — bidirectional)
# ═══════════════════════════════════════════════════════════════

def apply_neutral_correction(pred_class: int,
                              confidence: float,
                              polarity: float) -> dict:
    """Post-inference bidirectional neutral correction (v1 — TextBlob only).

    Kept for backward compatibility. New code should use apply_neutral_correction_v2.
    """
    neutral_corrected = False
    correction_reason = ""

    # MODE B: Neutral → Positive/Negative (primary fix for overcorrection)
    if (pred_class == 1
            and confidence < CONFIDENCE_THRESHOLD
            and abs(polarity) >= POLARITY_WEAK):
        if polarity > 0:
            new_class = 2  # Positive
        else:
            new_class = 0  # Negative
        logger.info(
            "Neutral elevation applied: Neutral → %s, conf=%.3f, pol=%.3f",
            LABEL_MAP.get(new_class, "?"), confidence, polarity,
        )
        correction_reason = (
            f"Strong polarity ({polarity:.3f}) overrides low-confidence Neutral ({confidence:.2f})"
        )
        pred_class = new_class
        neutral_corrected = True

    # MODE A: Positive/Negative → Neutral (original logic)
    elif (pred_class != 1
            and confidence < CONFIDENCE_THRESHOLD
            and abs(polarity) < POLARITY_WEAK):
        logger.info(
            "Neutral correction applied: pred=%s, conf=%.3f, pol=%.3f",
            LABEL_MAP.get(pred_class, "?"), confidence, polarity,
        )
        correction_reason = (
            f"Low confidence ({confidence:.2f}) with neutral polarity ({polarity:.3f})"
        )
        pred_class = 1
        neutral_corrected = True

    return {
        "pred_class": pred_class,
        "neutral_corrected": neutral_corrected,
        "correction_reason": correction_reason,
    }


# ═══════════════════════════════════════════════════════════════
# STEP 6b — Dual polarity (VADER + TextBlob)
# ═══════════════════════════════════════════════════════════════

def compute_dual_polarity(
    text: str,
    lang_code: str = "en",
) -> tuple:
    """Compute TextBlob polarity, VADER compound, and subjectivity.

    V5 RULESET 3 — STRICT ENGLISH-ONLY POLARITY:
      TextBlob/VADER run ONLY when lang_code == 'en'.
      For ALL other languages (even Latin-script ones), returns (0.0, 0.0, 0.5).
      This eliminates polarity-based neutral bias on multilingual content.
      XLM-R model handles classification natively for non-English.

    RULE 2 ENFORCEMENT: Original text only — translation never affects polarity.

    Args:
        text: Original review text (any language)
        lang_code: ISO 639-1 code

    Returns:
        (textblob_polarity, vader_compound, subjectivity)
    """
    if not text or not str(text).strip():
        return 0.0, 0.0, 0.5

    lang = (lang_code or "en").lower().strip()[:5]
    lc_short = lang[:2]

    # V5 RULESET 3: Only run TextBlob/VADER for English.
    # All other languages get neutral polarity defaults.
    if lc_short != "en":
        logger.debug(
            "[POLARITY SKIP] lang=%s — polarity skipped (English-only rule)", lang
        )
        return 0.0, 0.0, 0.5

    analysis_text = str(text)

    # TextBlob polarity
    tb_polarity = 0.0
    subjectivity = 0.5
    try:
        from textblob import TextBlob
        blob = TextBlob(analysis_text)
        tb_polarity = float(blob.sentiment.polarity)
        subjectivity = float(blob.sentiment.subjectivity)
    except Exception:
        pass

    # VADER compound
    vader_compound = 0.0
    if _VADER_AVAILABLE and _vader is not None:
        try:
            vader_compound = float(_vader.polarity_scores(analysis_text)["compound"])
        except Exception:
            pass

    return tb_polarity, vader_compound, subjectivity


def compute_polarity_from_label(label_name: str, confidence: float) -> float:
    """Derive a meaningful polarity score from model label + confidence.

    Section 3 FIX: TextBlob/VADER return 0.0 for non-English text,
    breaking the UI gauge. This function produces a polarity value
    that reflects the model's actual sentiment prediction:
        positive → +confidence  (e.g. +0.892)
        negative → -confidence  (e.g. -0.761)
        neutral  → 0.0

    This is used as the *display* polarity sent to the frontend.
    The raw TextBlob polarity is still used for VADER corrections
    on English text (internal only).
    """
    label = str(label_name).lower().strip()
    conf = max(0.0, min(1.0, float(confidence)))
    if label == "positive":
        return round(conf, 4)
    elif label == "negative":
        return round(-conf, 4)
    return 0.0


# ═══════════════════════════════════════════════════════════════
# STEP 6c — Neutral correction v2 (V4: MODEL-FIRST)
# ═══════════════════════════════════════════════════════════════

def apply_neutral_correction_v2(
    pred_class: int,
    confidence: float,
    tb_polarity: float,
    vader_compound: float,
    lang_code: str = "en",
) -> dict:
    """V6 model-first correction with English-only polarity fallback.

    confidence >= 0.65 keeps the model prediction. Below 0.65,
    English may use TextBlob polarity fallback; non-English always
    keeps the multilingual model label.
    """
    neutral_corrected = False
    correction_reason = ""
    lc = (lang_code or "en").lower().strip()[:2]

    # V6: High confidence -> model is final.
    if confidence >= 0.65:
        logger.debug(
            "[CORRECTION] Model-first: conf=%.3f >= 0.65, keeping label=%d",
            confidence, pred_class,
        )
        return {
            "pred_class": pred_class,
            "neutral_corrected": False,
            "correction_reason": "",
        }

    # V5 RULESET 3: Polarity only valid for English
    if lc != "en":
        logger.warning(
            "[CORRECTION] Low confidence (%.3f) for non-English lang=%s — "
            "keeping model label (polarity skipped per Ruleset 3)",
            confidence, lc,
        )
        logger.warning(
            "Low confidence fallback triggered (lang=%s, conf=%.3f)",
            lc, confidence,
        )
        return {
            "pred_class": pred_class,
            "neutral_corrected": False,
            "correction_reason": "",
        }

    # English + low confidence → polarity-based fallback
    polarity = tb_polarity

    if polarity > 0.25:
        new_class = 2  # Positive
    elif polarity < -0.25:
        new_class = 0  # Negative
    else:
        new_class = 1  # Neutral
        if pred_class != 1:
            logger.warning(
                "Neutral assigned due to low signal "
                "(conf=%.3f, polarity=%.3f)",
                confidence, polarity,
            )

    if new_class != pred_class:
        neutral_corrected = True
        correction_reason = (
            f"v5_low_conf_polarity_correction "
            f"(conf={confidence:.3f}, polarity={polarity:.3f})"
        )
        logger.info(
            "[CORRECTION] V5: %s → %s (conf=%.3f, polarity=%.3f)",
            LABEL_MAP.get(pred_class, "?"),
            LABEL_MAP.get(new_class, "?"),
            confidence,
            polarity,
        )

    return {
        "pred_class": new_class,
        "neutral_corrected": neutral_corrected,
        "correction_reason": correction_reason,
    }


# ═══════════════════════════════════════════════════════════════
# STEP 7 — Confidence calibration (Problem 5)
# ═══════════════════════════════════════════════════════════════

def calibrated_confidence(confidence: float,
                           polarity: float = 0.0,
                           pred_class: int = 1) -> float:
    """V4 FIX 2: No artificial confidence reduction.

    The raw softmax confidence from the model is the true confidence.
    Any reduction compounds with XLM-R's naturally lower confidence
    (~44%) and triggers incorrect neutral overrides.

    Returns the confidence unchanged, clamped to [0.0, 1.0].
    polarity and pred_class args retained for API signature compat.
    """
    try:
        confidence = float(confidence)
    except Exception:
        confidence = 0.0
    return round(max(0.0, min(1.0, confidence)), 4)


# ═══════════════════════════════════════════════════════════════
# STEP 8 — Temperature scaling (ADD-ON 5)
# ═══════════════════════════════════════════════════════════════

def apply_temperature_scaling(logits: list[float],
                               temperature: float = CALIBRATION_TEMPERATURE
                               ) -> list[float]:
    """Temperature scaling for softmax recalibration.

    Reduces overconfident boundary-zone predictions from 85–92% to ~70–78%.
    Only apply when RoBERTa returns full logit/score array.
    """
    scaled = [l / temperature for l in logits]
    max_scaled = max(scaled)
    exp_scaled = [math.exp(s - max_scaled) for s in scaled]
    total = sum(exp_scaled)
    return [e / total for e in exp_scaled]


# ═══════════════════════════════════════════════════════════════
# STEP 10.5 — Sarcasm → sentiment override
# ═══════════════════════════════════════════════════════════════

def _apply_sarcasm_override(pred_class: int,
                             confidence: float,
                             is_sarcastic: bool,
                             sarcasm_confidence: float = 0.0) -> dict:
    """Override Positive/weak-Neutral → Negative when sarcasm is detected.

    Flips when:
      1. Sarcasm detected (is_sarcastic=True)
      2. Sarcasm confidence >= 0.65
      3. Predicted Positive (2) with confidence < 0.90, OR
         Predicted Neutral (1) with confidence < 0.75 (weak Neutral)
      4. Never flips Negative — sarcasm on Negative is uncommon

    Returns dict with updated pred_class, sarcasm_applied flag.
    """
    sarcasm_applied = False
    if is_sarcastic and sarcasm_confidence >= 0.65:
        if pred_class == 2 and confidence < 0.90:
            # High-confidence Positive + sarcasm → Negative
            old_label = LABEL_MAP.get(pred_class, "?")
            pred_class = 0
            confidence = round(sarcasm_confidence * 0.85, 4)
            sarcasm_applied = True
            logger.info(
                "Sarcasm override: %s → %s (sarcasm_conf=%.2f)",
                old_label, LABEL_MAP[pred_class], sarcasm_confidence,
            )
        elif pred_class == 1 and confidence < 0.75:
            # Weak Neutral + sarcasm → Negative
            old_label = LABEL_MAP.get(pred_class, "?")
            pred_class = 0
            confidence = round(sarcasm_confidence * 0.85, 4)
            sarcasm_applied = True
            logger.info(
                "Sarcasm override (weak Neutral): %s → %s (sarcasm_conf=%.2f)",
                old_label, LABEL_MAP[pred_class], sarcasm_confidence,
            )
        # Never flip Negative — sarcasm on Negative is uncommon and risky

    return {
        "pred_class": pred_class,
        "confidence": confidence,
        "sarcasm_applied": sarcasm_applied,
    }


# ═══════════════════════════════════════════════════════════════
# MAIN — predict_sentiment (full pipeline)
# ═══════════════════════════════════════════════════════════════

def predict_sentiment(text, model_pipeline=None, run_sarcasm_detection=True):
    """Predict sentiment using RoBERTa transformer model.

    The model_pipeline argument is kept for backward compatibility
    but is ignored — the transformer model is used instead.

    Full post-processing pipeline (ADD-ON 10 wiring contract):
      Step 0:  Input safety guard
      Step 1:  Preprocess text
      Step 2:  model.predict() → raw pred_class
      Step 3:  Compute raw_confidence
      Step 4:  Compute TextBlob polarity + subjectivity
      Step 5:  apply_short_text_guard()
      Step 6:  apply_neutral_correction()
      Step 7:  calibrated_confidence()
      Step 8:  apply_temperature_scaling() (conditional)
      Step 9:  label_name = LABEL_MAP[pred_class]
      Step 10: Sarcasm detection + override
      Step 11: Uncertainty flag
      Step 12: Return complete result dict (20 fields)

    Returns dict with ALL 20 required fields.
    """
    # Step 0: Input safety guard
    guard = _input_safety_guard(text)
    if guard:
        return guard

    from src.models.sentiment import predict as transformer_predict

    # Step 0.5: Single-word pre-uncertainty flag
    original_text = str(text).strip()
    pre_uncertain = len(original_text.split()) == 1 and len(original_text) < 15

    # Determine language code for hard model routing.
    # model_pipeline may be a UI model choice ("best") or a language code.
    lang_code = "en"
    if isinstance(model_pipeline, str):
        candidate = model_pipeline.lower().strip()
        model_choices = {
            "best", "linearsvc", "logisticregression",
            "naivebayes", "randomforest",
        }
        if candidate and candidate not in model_choices:
            lang_code = candidate

    # Step 2: Run model prediction → raw pred_class and logits/scores
    result = transformer_predict(original_text, lang_code=lang_code)
    pred_class = result["label"]
    scores = result["scores"]  # [neg, neu, pos]
    model_used = result.get(
        "model_used", "roberta" if lang_code[:2] == "en" else "xlm-r"
    )

    # Step 3: Compute raw_confidence
    raw_confidence = result["confidence"]

    # ── V4+ STABILITY LOCK: Margin-based decision ───────────
    pred_class, margin, decision_type = apply_decision_layer(scores, LABEL_MAP)

    # ── Short-text keyword guard (safety net) ────────────────
    guard_result = apply_short_text_guard(original_text, pred_class, raw_confidence)
    pred_class = guard_result["pred_class"]
    guard_applied = guard_result["guard_applied"]

    # ── Entropy-based calibrated confidence ──────────────────
    confidence = compute_calibrated_confidence(scores)

    # Step 8.5: V4 — Ensemble penalties REMOVED.

    # Step 8.9: V4 ADD-ON 1 — Protect confident Positive/Negative labels
    protected_label = LABEL_MAP[pred_class]
    was_protected = False
    if pred_class in (0, 2) and raw_confidence >= 0.45:
        was_protected = True
        logger.debug(
            "[PROTECTION] Label %s protected (raw_conf=%.3f >= 0.45)",
            LABEL_MAP[pred_class], raw_confidence,
        )

    # Step 9: label_name from LABEL_MAP (NEVER from raw string)
    label_name = LABEL_MAP[pred_class]

    # Step 10: Sarcasm detection + override
    sarcasm_detected = False
    sarcasm_confidence_val = 0.0
    sarcasm_applied = False
    sarcasm_reason = ""

    if run_sarcasm_detection:
        try:
            from src.sarcasm_detector import detect_sarcasm
            sarcasm_result = detect_sarcasm(original_text, pred_class)
            sarcasm_detected = sarcasm_result.get("is_sarcastic", False)
            sarcasm_confidence_val = sarcasm_result.get("confidence", 0.0)
            sarcasm_reason = sarcasm_result.get("reason", "")

            # Step 10.5: Sarcasm → sentiment override
            override = _apply_sarcasm_override(
                pred_class, confidence, sarcasm_detected, sarcasm_confidence_val
            )
            pred_class = override["pred_class"]
            confidence = override["confidence"]
            sarcasm_applied = override["sarcasm_applied"]

            # Re-derive label_name after potential flip
            if sarcasm_applied:
                label_name = LABEL_MAP[pred_class]
        except Exception as e:
            logger.warning("Sarcasm detection failed: %s", e)

    # Step 11: V3 structured logging (uncertainty is metadata only)
    low_confidence = pre_uncertain or confidence < CONFIDENCE_UNCERTAIN_THRESHOLD
    if low_confidence:
        logger.debug(
            "Low confidence prediction: label=%s conf=%.4f threshold=%.2f",
            label_name, confidence, CONFIDENCE_UNCERTAIN_THRESHOLD,
        )

    # Step 12: V4 ADD-ON 3 — Reliability signal (display only, never changes label)
    _rel_conf = float(confidence)
    if _rel_conf >= 0.80:
        reliability = "high"
    elif _rel_conf >= 0.55:
        reliability = "moderate"
    else:
        reliability = "low"

    # Step 13: Compute display polarity from label + confidence
    display_polarity = compute_polarity_from_label(label_name, confidence)

    # Step 14: Return complete result dict
    return {
        "label": pred_class,
        "label_name": label_name,
        "confidence": float(confidence),
        "raw_confidence": float(raw_confidence),
        "polarity": display_polarity,
        "subjectivity": 0.5,
        "neutral_corrected": False,
        "correction_reason": "",
        "guard_applied": guard_applied,
        "temperature_scaled": False,
        "translation_status": "OK",
        "translation_flagged": False,
        "translation_failed": False,
        "hinglish_detected": False,
        "analysis_input_source": "original",
        "model_used": model_used,
        "was_protected": was_protected,
        "margin": round(margin, 4),
        "decision_type": decision_type,
        "reliability": reliability,
        "sarcasm_detected": sarcasm_detected,
        "sarcasm_confidence": float(sarcasm_confidence_val),
        "sarcasm_applied": sarcasm_applied,
        "sarcasm_reason": sarcasm_reason,
    }


def load_model(model_name="best"):
    """Backward-compatible model loader.

    Returns (None, label_map) — the transformer model is loaded
    internally by predict_sentiment() and cached via @st.cache_resource.
    """
    return None, dict(LABEL_MAP)
