"""V6 critical correction layer tests."""

from types import SimpleNamespace

import pytest


def test_hard_model_routing():
    from src.models.sentiment import _detect_model_for_lang

    assert _detect_model_for_lang("en") == "roberta"
    for lang in ["fr", "de", "es", "hi", "ar", "ja", "zh-cn", "unknown"]:
        assert _detect_model_for_lang(lang) == "xlm-r"


def test_translation_validation_contract():
    from src.models.translation import LANG_MAP, validate_translation

    assert LANG_MAP["hi"] == "hin_Deva"
    assert LANG_MAP["ar"] == "arb_Arab"
    assert LANG_MAP["fr"] == "fra_Latn"
    assert LANG_MAP["de"] == "deu_Latn"
    assert LANG_MAP["es"] == "spa_Latn"
    assert LANG_MAP["it"] == "ita_Latn"
    assert LANG_MAP["pt"] == "por_Latn"
    assert LANG_MAP["ja"] == "jpn_Jpan"
    assert LANG_MAP["zh"] == "zho_Hans"

    assert validate_translation("bonjour", "hello")
    assert not validate_translation("bonjour", "")
    assert not validate_translation("bonjour", "hi")
    assert not validate_translation("bonjour", "bonjour")
    assert not validate_translation("bonjour", "[Translated] hello")


def test_nllb_forces_english_bos(monkeypatch):
    import src.models.translation as translation

    class FakeTokenizer:
        lang_code_to_id = {"eng_Latn": 123}

        def __init__(self):
            self.src_lang = None

        def __call__(self, texts, **kwargs):
            self.texts = texts
            self.kwargs = kwargs
            return {"input_ids": [[1]], "attention_mask": [[1]]}

        def batch_decode(self, tokens, skip_special_tokens=True):
            return ["hello"]

    class FakeModel:
        def generate(self, **kwargs):
            assert kwargs["forced_bos_token_id"] == 123
            assert kwargs["max_length"] == 256
            return [[1, 2, 3]]

    fake_tokenizer = FakeTokenizer()
    monkeypatch.setattr(translation, "_load_nllb", lambda: True)
    monkeypatch.setattr(translation, "_nllb_tokenizer", fake_tokenizer)
    monkeypatch.setattr(translation, "_nllb_model", FakeModel())

    assert translation._translate_nllb("bonjour", "fr") == "hello"
    assert fake_tokenizer.src_lang == "fra_Latn"


def test_raw_single_batch_consistency(monkeypatch):
    torch = pytest.importorskip("torch")
    import src.models.sentiment as sentiment

    class FakeTokenizer:
        def __call__(self, texts, **kwargs):
            batch = len(texts) if isinstance(texts, list) else 1
            return {
                "input_ids": torch.ones((batch, 2), dtype=torch.long),
                "attention_mask": torch.ones((batch, 2), dtype=torch.long),
            }

    class FakeModel:
        def parameters(self):
            yield torch.zeros(1)

        def __call__(self, **inputs):
            batch = inputs["input_ids"].shape[0]
            logits = torch.tensor([[0.1, 0.2, 3.0]] * batch)
            return SimpleNamespace(logits=logits)

    fake_pair = (FakeTokenizer(), FakeModel())
    monkeypatch.setattr(sentiment, "_load_model", lambda model_id: fake_pair)

    single = sentiment.predict("Ce produit est excellent", lang_code="fr")
    batch = sentiment.predict_batch(
        ["Ce produit est excellent"],
        lang_codes=["fr"],
    )[0]

    assert single["label_name"].lower() == batch["label_name"].lower()
    assert abs(single["confidence"] - batch["confidence"]) < 0.01
    assert single["model_used"] == batch["model_used"] == "xlm-r"


def test_pipeline_batch_groups_translation(monkeypatch):
    import src.pipeline.inference as inference

    calls = []

    def fake_detect_language(text):
        return {
            "code": "fr",
            "name": "French",
            "flag_emoji": "FR",
            "hinglish_detected": False,
        }

    def fake_translate_batch(texts, src_lang):
        calls.append((src_lang, list(texts)))
        return [f"translated {i}" for i, _ in enumerate(texts)]

    def fail_safe_translate(*args, **kwargs):
        raise AssertionError("batch pipeline must not call per-item translation")

    def fake_sentiment_batch(texts, lang_codes):
        return [
            {
                "label": 2,
                "label_name": "Positive",
                "confidence": 0.9,
                "scores": [0.01, 0.09, 0.90],
                "model_used": "xlm-r",
            }
            for _ in texts
        ]

    def fake_postprocess(text, sentiment, lang_code="en", translated_text=""):
        assert translated_text == ""
        return {
            "label": 2,
            "label_name": "Positive",
            "sentiment": "Positive",
            "confidence": 0.82,
            "raw_confidence": 0.9,
            "scores": [0.01, 0.09, 0.90],
            "polarity": 0.0,
            "subjectivity": 0.5,
            "neutral_corrected": False,
            "correction_reason": "",
            "guard_applied": False,
            "temperature_scaled": False,
        }

    monkeypatch.setattr(inference, "detect_language", fake_detect_language)
    monkeypatch.setattr(inference, "translate_batch", fake_translate_batch)
    monkeypatch.setattr(inference, "safe_translate", fail_safe_translate)
    monkeypatch.setattr(inference, "sentiment_predict_batch", fake_sentiment_batch)
    monkeypatch.setattr(inference, "_apply_post_processing", fake_postprocess)
    monkeypatch.setattr(
        inference,
        "detect_sarcasm_bulk",
        lambda *args, **kwargs: {
            "is_sarcastic": False,
            "confidence": 0.0,
            "reason": "",
        },
    )
    monkeypatch.setattr(
        inference,
        "_apply_sarcasm_override",
        lambda label, confidence, is_sarc, sarc_conf: {
            "sarcasm_applied": False,
            "pred_class": label,
            "confidence": confidence,
        },
    )

    results = inference.run_pipeline_batch(["bon produit", "excellent service"])

    assert calls == [("fr", ["bon produit", "excellent service"])]
    assert [r["translated"] for r in results] == ["translated 0", "translated 1"]
    assert [r["analysis_input_source"] for r in results] == ["original", "original"]
