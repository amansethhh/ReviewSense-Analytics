import pytest


def test_metrics_structure(client):
    r = client.get("/metrics")
    assert r.status_code == 200
    data = r.json()
    assert len(data["models"]) == 4
    best = next(m for m in data["models"]
                if m["is_best"])
    assert best["name"] == "LinearSVC"
    assert abs(best["accuracy"] - 95.80) < 0.01
    assert abs(best["macro_f1"] - 0.5742) < 0.001
    assert data["best_model"] == "LinearSVC (Offline Only)"
    assert len(data["confusion_matrices"]) == 4


def test_metrics_all_models_present(client):
    r = client.get("/metrics")
    names = [m["name"] for m in r.json()["models"]]
    assert "LinearSVC" in names
    assert "Logistic Regression" in names
    assert "Naive Bayes" in names
    assert "Random Forest" in names
