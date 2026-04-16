"""
Tests for the feedback endpoint.
"""
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_submit_feedback():
    """Submit a simple feedback entry."""
    r = client.post("/feedback/submit", json={
        "text": "Good product",
        "predicted_sentiment": "positive",
        "correct_sentiment": "positive",
        "confidence": 85.0,
        "source": "live_prediction",
    })
    assert r.status_code == 200
    data = r.json()
    assert "feedback_id" in data
    assert data["total_feedback_collected"] >= 1


def test_submit_correction_feedback():
    """Submit a correction (predicted != correct)."""
    r = client.post("/feedback/submit", json={
        "text": "not bad",
        "predicted_sentiment": "negative",
        "correct_sentiment": "neutral",
        "confidence": 73.8,
        "source": "live_prediction",
    })
    assert r.status_code == 200
    data = r.json()
    assert "feedback_id" in data


def test_feedback_stats():
    """Stats endpoint returns expected fields."""
    r = client.get("/feedback/stats")
    assert r.status_code == 200
    data = r.json()
    assert "total_feedback" in data
    assert "corrections" in data
    assert "correction_rate_pct" in data
    assert "by_source" in data
