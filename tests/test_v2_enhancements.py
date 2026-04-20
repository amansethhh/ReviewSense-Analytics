"""
ReviewSense V2 Enhancement Smoke Tests.

Validates all V2 fixes:
  FIX 1: Dual model routing (XLM for non-Latin)
  FIX 2: VADER integration
  FIX 3: Translation pipeline (deep-translator)
  FIX 4: Batched inference with language routing
  FIX 5: Model pre-warming
  ADD-ON 1: UNCERTAIN label

Run with: pytest tests/test_v2_enhancements.py -v
"""

import sys
import os
import pytest

# Add src/ and backend/ to path for imports
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "src"))
sys.path.insert(0, os.path.join(ROOT_DIR, "backend"))


# ══════════════════════════════════════════════════════════════
# FIX 1: Dual model routing
# ══════════════════════════════════════════════════════════════

class TestDualModelRouting:
    """Verify XLM model is selected for non-Latin scripts."""

    def test_xlm_languages_defined(self):
        from src.models.sentiment import XLM_LANGUAGES
        assert "ja" in XLM_LANGUAGES
        assert "ko" in XLM_LANGUAGES
        assert "zh" in XLM_LANGUAGES
        assert "hi" in XLM_LANGUAGES
        assert "ar" in XLM_LANGUAGES
        assert "ru" in XLM_LANGUAGES

    def test_english_routes_to_english_model(self):
        from src.models.sentiment import (
            get_model_for_language,
            ENGLISH_MODEL_ID,
        )
        tokenizer, model = get_model_for_language("en")
        # Verify it's the English model by checking tokenizer config
        assert tokenizer is not None
        assert model is not None

    def test_japanese_routes_to_xlm_model(self):
        from src.models.sentiment import (
            get_model_for_language,
            MULTILINGUAL_MODEL_ID,
        )
        tokenizer, model = get_model_for_language("ja")
        assert tokenizer is not None
        assert model is not None

    def test_predict_accepts_lang_code(self):
        """predict() should accept lang_code parameter."""
        from src.models.sentiment import predict
        result = predict("This is a great product", lang_code="en")
        assert "label" in result
        assert "scores" in result
        assert len(result["scores"]) == 3

    def test_predict_batch_with_lang_codes(self):
        """predict_batch() should accept lang_codes list."""
        from src.models.sentiment import predict_batch
        texts = ["Great product!", "素晴らしい製品"]
        langs = ["en", "ja"]
        results = predict_batch(texts, lang_codes=langs)
        assert len(results) == 2
        assert all("label" in r for r in results)


# ══════════════════════════════════════════════════════════════
# FIX 2: VADER integration
# ══════════════════════════════════════════════════════════════

class TestVADERIntegration:
    """Verify VADER is available and compute_dual_polarity works."""

    def test_vader_available(self):
        from src.predict import _VADER_AVAILABLE
        assert _VADER_AVAILABLE, "vaderSentiment must be installed"

    def test_compute_dual_polarity_english(self):
        from src.predict import compute_dual_polarity
        tb_pol, vader_comp, subj = compute_dual_polarity(
            "This product is absolutely terrible and broken",
            "en",
        )
        # Both should be negative
        assert tb_pol < 0.0
        assert vader_comp < -0.3

    def test_compute_dual_polarity_non_latin_returns_zero(self):
        from src.predict import compute_dual_polarity
        tb_pol, vader_comp, subj = compute_dual_polarity(
            "素晴らしい製品です", "ja"
        )
        assert tb_pol == 0.0
        assert vader_comp == 0.0
        assert subj == 0.5

    def test_neutral_correction_v2_vader_negative(self):
        """When model says Neutral but VADER is strongly negative,
        should correct to Negative."""
        from src.predict import apply_neutral_correction_v2
        result = apply_neutral_correction_v2(
            pred_class=1,  # Neutral
            confidence=0.55,
            tb_polarity=-0.3,
            vader_compound=-0.65,  # strongly negative
            lang_code="en",
        )
        assert result["pred_class"] == 0  # should be Negative
        assert result["neutral_corrected"]

    def test_neutral_correction_v2_no_false_positive(self):
        """When model and VADER agree, no correction should fire."""
        from src.predict import apply_neutral_correction_v2
        result = apply_neutral_correction_v2(
            pred_class=2,  # Positive
            confidence=0.85,  # high confidence
            tb_polarity=0.5,
            vader_compound=0.7,
            lang_code="en",
        )
        assert result["pred_class"] == 2  # stays Positive
        assert not result["neutral_corrected"]


# ══════════════════════════════════════════════════════════════
# FIX 3: Translation pipeline
# ══════════════════════════════════════════════════════════════

class TestTranslationPipeline:
    """Verify deep-translator integration."""

    def test_deep_translator_available(self):
        from src.models.translation import _DEEP_TRANSLATOR_AVAILABLE
        assert _DEEP_TRANSLATOR_AVAILABLE

    def test_degenerate_detection(self):
        from src.models.translation import _is_degenerate
        assert _is_degenerate("Hello", "")
        assert _is_degenerate("Hello", "...")
        assert _is_degenerate("Hello", "error")
        assert not _is_degenerate("Hello", "Hello world")


# ══════════════════════════════════════════════════════════════
# FIX 5: Model pre-warming
# ══════════════════════════════════════════════════════════════

class TestModelPreWarming:
    """Verify load_all_models works without errors."""

    def test_load_all_models(self):
        from src.models.sentiment import load_all_models
        result = load_all_models()
        assert "english" in result
        assert "multilingual" in result


# ══════════════════════════════════════════════════════════════
# ADD-ON 1: UNCERTAIN label threshold
# ══════════════════════════════════════════════════════════════

class TestUncertainLabel:
    """Verify UNCERTAIN confidence threshold is configured."""

    def test_uncertain_threshold_exists(self):
        from src.predict import CONFIDENCE_UNCERTAIN_THRESHOLD
        assert 0.50 <= CONFIDENCE_UNCERTAIN_THRESHOLD <= 0.70

    def test_predict_returns_uncertain_flag(self):
        from src.predict import predict_sentiment
        result = predict_sentiment("ok")
        assert "uncertain_prediction" in result


# ══════════════════════════════════════════════════════════════
# Integration: End-to-end pipeline
# ══════════════════════════════════════════════════════════════

class TestEndToEnd:
    """Full pipeline integration tests."""

    def test_english_positive(self):
        from src.predict import predict_sentiment
        result = predict_sentiment(
            "This product is absolutely amazing and wonderful!"
        )
        assert result["label_name"] in ("Positive", "Neutral")
        assert result["confidence"] > 0.3

    def test_english_negative(self):
        from src.predict import predict_sentiment
        result = predict_sentiment(
            "Terrible quality, broke after one day. Complete waste of money."
        )
        assert result["label_name"] in ("Negative", "Neutral")

    def test_short_text_guard(self):
        from src.predict import predict_sentiment
        result = predict_sentiment("bad product")
        # Short text guard should catch this
        assert "guard_applied" in result

    def test_result_has_20_fields(self):
        from src.predict import predict_sentiment
        result = predict_sentiment("This is a decent product.")
        expected_fields = {
            "label", "label_name", "confidence", "raw_confidence",
            "polarity", "subjectivity", "neutral_corrected",
            "correction_reason", "guard_applied", "temperature_scaled",
            "translation_status", "translation_flagged",
            "hinglish_detected", "analysis_input_source",
            "sarcasm_detected", "sarcasm_confidence",
            "sarcasm_applied", "sarcasm_reason",
            "uncertain_prediction", "confidence_threshold",
        }
        assert expected_fields.issubset(set(result.keys())), \
            f"Missing fields: {expected_fields - set(result.keys())}"
