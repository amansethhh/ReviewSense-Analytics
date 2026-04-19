"""
Phase 6 GAP 4: Tests that the language route degrades gracefully
when all translation tiers fail.

These tests use mocks — no real network access required.
The model dependency is mocked to avoid startup loading requirement.
"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app


def _make_fake_model():
    """Return a minimal mock model object."""
    return MagicMock()


def _make_fake_pred():
    """Return a plausible predict_sentiment result."""
    return {
        "label_name": "Positive",
        "confidence": 0.87,
        "polarity": 0.8,
        "subjectivity": 0.9,
        "model_used": "LinearSVC",
    }


@pytest.fixture(autouse=True)
def mock_model_deps():
    """
    Globally mock ML model dependencies so tests run without
    the full startup sequence. Applied to every test in this module.
    """
    with patch(
        "backend.app.dependencies.load_artifacts",
        return_value=None,
    ), patch(
        "backend.app.dependencies._model",
        _make_fake_model(),
    ), patch(
        "backend.app.dependencies._vectorizer",
        _make_fake_model(),
    ), patch(
        "backend.app.dependencies._models_loaded",
        True,
    ), patch(
        "src.predict.predict_sentiment",
        return_value=_make_fake_pred(),
    ):
        yield


def test_language_route_when_translation_fails():
    """
    When both Helsinki-NLP AND Google Translate fail, the route
    must still return HTTP 200 with a valid sentiment result.
    Tier 3 (raw predict on original text) should handle this.
    """
    client = TestClient(app)
    with patch(
        "backend.app.utils.translation_client._google_translate_with_timeout",
        side_effect=Exception("network error"),
    ), patch(
        "src.translator.detect_and_translate",
        side_effect=Exception("helsinki unavailable"),
    ):
        resp = client.post(
            "/language",
            json={"text": "Este producto es excelente", "model": "best"},
        )

    assert resp.status_code == 200, (
        f"Expected 200, got {resp.status_code}: {resp.text}")
    data = resp.json()
    assert data["sentiment"] in (
        "positive", "negative", "neutral", "unknown", "error"
    ), f"Unexpected sentiment: {data['sentiment']}"
    assert "confidence" in data


def test_language_route_timeout_returns_result():
    """
    When _google_translate_with_timeout raises TimeoutError,
    the route must still return HTTP 200 via Tier 3 raw predict.
    """
    client = TestClient(app)
    with patch(
        "backend.app.utils.translation_client._google_translate_with_timeout",
        side_effect=TimeoutError("timeout"),
    ), patch(
        "src.translator.detect_and_translate",
        side_effect=Exception("helsinki timeout"),
    ):
        resp = client.post(
            "/language",
            json={"text": "Este producto es excelente", "model": "best"},
        )

    assert resp.status_code == 200, (
        f"Expected 200, got {resp.status_code}: {resp.text}")
    data = resp.json()
    assert data["sentiment"] in (
        "positive", "negative", "neutral", "unknown", "error"
    ), f"Unexpected sentiment: {data['sentiment']}"
