import pytest


def test_language_detect_english(client):
    r = client.post("/language", json={
        "text": "This is a great product.",
        "model": "best",
    })
    assert r.status_code == 200
    data = r.json()
    assert "detected_language" in data
    assert "language_code" in data
    assert "sentiment" in data
    assert data["sentiment"] in [
        "positive", "negative", "neutral"]
    assert "confidence" in data
    assert "processing_ms" in data


def test_language_empty_text_rejected(client):
    r = client.post("/language",
                    json={"text": "   "})
    assert r.status_code == 422


def test_language_response_has_translation_flag(client):
    r = client.post("/language", json={
        "text": "Excellent quality and fast shipping!",
    })
    assert r.status_code == 200
    data = r.json()
    assert "translation_needed" in data
    assert isinstance(data["translation_needed"], bool)
