"""
W4-4: Unit tests for translate_with_retry function.

Tests:
1. Success on first attempt
2. Retry then success (fail once, succeed second)
3. All retries exhausted (fail all 3)
4. Empty result triggers retry
"""

from unittest.mock import patch, MagicMock
import pytest


def _get_fresh_translate():
    """
    Import translate_with_retry fresh each time to avoid
    cached module-level state between tests.
    """
    from app.utils.translation_client import (
        translate_with_retry,
    )
    return translate_with_retry


def test_translate_success_first_attempt():
    """Translation succeeds on first call — no retries."""
    mock_translator = MagicMock()
    mock_translator.return_value.translate.return_value = (
        "Great product!"
    )

    with patch(
        "deep_translator.GoogleTranslator",
        mock_translator,
    ):
        translate_with_retry = _get_fresh_translate()
        text, status = translate_with_retry(
            "Excelente producto!", "es", "en"
        )

    assert status == "success"
    assert text == "Great product!"
    assert mock_translator.return_value.translate.call_count == 1


def test_translate_retry_then_success():
    """First attempt fails, second succeeds."""
    mock_translator = MagicMock()
    mock_translator.return_value.translate.side_effect = [
        Exception("Network error"),
        "Good product!",
    ]

    with patch(
        "deep_translator.GoogleTranslator",
        mock_translator,
    ), patch(
        "time.sleep",
    ):
        translate_with_retry = _get_fresh_translate()
        text, status = translate_with_retry(
            "Buen producto!", "es", "en"
        )

    assert status == "success"
    assert text == "Good product!"
    # Called twice: first fail, second success
    assert mock_translator.return_value.translate.call_count == 2


def test_translate_all_retries_exhausted():
    """All 3 attempts fail — returns original text + 'failed'."""
    mock_translator = MagicMock()
    mock_translator.return_value.translate.side_effect = (
        Exception("API down")
    )

    with patch(
        "deep_translator.GoogleTranslator",
        mock_translator,
    ), patch(
        "time.sleep",
    ):
        translate_with_retry = _get_fresh_translate()
        text, status = translate_with_retry(
            "Producto terrible!", "es", "en"
        )

    assert status == "failed"
    assert text == "Producto terrible!"
    assert mock_translator.return_value.translate.call_count == 3


def test_translate_empty_result_triggers_retry():
    """Empty string results trigger retry."""
    mock_translator = MagicMock()
    mock_translator.return_value.translate.side_effect = [
        "",       # Empty — should retry
        "   ",    # Whitespace only — should retry
        "Good!",  # Third attempt succeeds
    ]

    with patch(
        "deep_translator.GoogleTranslator",
        mock_translator,
    ), patch(
        "time.sleep",
    ):
        translate_with_retry = _get_fresh_translate()
        text, status = translate_with_retry(
            "Bueno!", "es", "en"
        )

    assert status == "success"
    assert text == "Good!"
    assert mock_translator.return_value.translate.call_count == 3
