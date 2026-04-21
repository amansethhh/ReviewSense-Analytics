"""NLLB-only translation client tests."""

from unittest.mock import patch


def _get_fresh_translate():
    from app.utils.translation_client import translate_with_retry

    return translate_with_retry


def test_translate_success_from_nllb():
    with patch(
        "src.models.translation.translate_to_english",
        return_value=("Great product!", "nllb"),
    ) as mock_translate:
        translate_with_retry = _get_fresh_translate()
        text, status = translate_with_retry(
            "Excelente producto!", "es", "en"
        )

    assert status == "success"
    assert text == "Great product!"
    mock_translate.assert_called_once_with("Excelente producto!", "es")


def test_translate_cache_success():
    with patch(
        "src.models.translation.translate_to_english",
        return_value=("Good product!", "cache"),
    ):
        translate_with_retry = _get_fresh_translate()
        text, status = translate_with_retry("Buen producto!", "es", "en")

    assert status == "success"
    assert text == "Good product!"


def test_translate_passthrough_success_for_english():
    with patch(
        "src.models.translation.translate_to_english",
        return_value=("Already English", "passthrough"),
    ):
        translate_with_retry = _get_fresh_translate()
        text, status = translate_with_retry("Already English", "en", "en")

    assert status == "success"
    assert text == "Already English"


def test_translate_nllb_failure_returns_original():
    with patch(
        "src.models.translation.translate_to_english",
        return_value=("Producto terrible!", "passthrough_failed"),
    ):
        translate_with_retry = _get_fresh_translate()
        text, status = translate_with_retry(
            "Producto terrible!", "es", "en"
        )

    assert status == "failed"
    assert text == "Producto terrible!"
