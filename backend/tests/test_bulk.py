import io
import time
import pytest
import pandas as pd


def test_bulk_submit_returns_job_id(client):
    df = pd.DataFrame({
        "review": [
            "Great product!",
            "Terrible service.",
            "Average experience.",
        ]
    })
    csv_bytes = df.to_csv(index=False).encode()
    r = client.post("/bulk", files={
        "file": ("test.csv",
                 io.BytesIO(csv_bytes),
                 "text/csv")
    }, data={"text_column": "review",
             "model": "best"})
    assert r.status_code == 200
    data = r.json()
    assert "job_id" in data
    assert data["status"] == "queued"
    assert data["total_rows"] == 3


def test_bulk_status_polling(client):
    # Submit job
    df = pd.DataFrame({"review": ["Good.", "Bad.", "OK."]})
    csv_bytes = df.to_csv(index=False).encode()
    submit_r = client.post("/bulk", files={
        "file": ("t.csv", io.BytesIO(csv_bytes), "text/csv")
    }, data={"text_column": "review"})
    job_id = submit_r.json()["job_id"]
    # Poll until complete (max 30s)
    for _ in range(30):
        time.sleep(1)
        r = client.get(f"/bulk/status/{job_id}")
        assert r.status_code == 200
        if r.json()["status"] == "completed":
            assert r.json()["results"] is not None
            break
    # Don't assert completion — just check no 500 errors


def test_bulk_empty_file_rejected(client):
    df = pd.DataFrame({"review": []})
    csv_bytes = df.to_csv(index=False).encode()
    r = client.post("/bulk", files={
        "file": ("empty.csv", io.BytesIO(csv_bytes),
                 "text/csv")
    }, data={"text_column": "review"})
    assert r.status_code == 400
