import pytest


POSITIVE_INPUTS = [
    "The food was absolutely amazing and delicious.",
    "Outstanding service, I loved every moment.",
    "Best product I have ever purchased, highly recommend.",
]
NEGATIVE_INPUTS = [
    "Terrible experience, complete waste of money.",
    "The worst service I have ever encountered.",
    "Broken on arrival, very disappointed.",
]


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] in ["healthy", "degraded"]


def test_predict_returns_valid_structure(client):
    r = client.post("/predict", json={
        "text": "The food was amazing.",
        "model": "best",
        "include_lime": False,
        "include_absa": False,
        "include_sarcasm": False,
    })
    assert r.status_code == 200
    data = r.json()
    assert "sentiment" in data
    assert data["sentiment"] in [
        "positive", "negative", "neutral"]
    assert "confidence" in data
    assert 0 <= data["confidence"] <= 100
    assert "polarity" in data
    assert "subjectivity" in data
    assert "processing_ms" in data


def test_predict_positive_inputs(client):
    for text in POSITIVE_INPUTS:
        r = client.post("/predict", json={
            "text": text, "model": "best",
            "include_lime": False,
            "include_absa": False,
            "include_sarcasm": False,
        })
        assert r.status_code == 200


def test_predict_empty_text_rejected(client):
    r = client.post("/predict",
                    json={"text": "   "})
    assert r.status_code == 422


def test_predict_with_lime(client):
    r = client.post("/predict", json={
        "text": "Amazing product, loved it!",
        "include_lime": True,
        "include_absa": False,
        "include_sarcasm": False,
    })
    assert r.status_code == 200
    data = r.json()
    if data.get("lime_features"):
        assert isinstance(data["lime_features"], list)
        for f in data["lime_features"]:
            assert "word" in f
            assert "weight" in f


def test_predict_with_absa(client):
    r = client.post("/predict", json={
        "text": "Camera is great but battery is terrible.",
        "include_lime": False,
        "include_absa": True,
        "include_sarcasm": False,
    })
    assert r.status_code == 200


def test_predict_confidence_tolerance(client):
    """
    Run the same input twice.
    Confidence must be within ±1.0 (deterministic model).
    """
    payload = {
        "text": "The service was excellent.",
        "model": "best",
        "include_lime": False,
        "include_absa": False,
        "include_sarcasm": False,
    }
    r1 = client.post("/predict", json=payload)
    r2 = client.post("/predict", json=payload)
    assert r1.status_code == 200
    assert r2.status_code == 200
    diff = abs(r1.json()["confidence"] -
               r2.json()["confidence"])
    assert diff < 1.0, (
        f"Confidence not deterministic: "
        f"{r1.json()['confidence']} vs "
        f"{r2.json()['confidence']}"
    )
