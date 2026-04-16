"""
Tests for bulk export endpoint.
"""
import time
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_export_nonexistent_job():
    """404 for a job ID that doesn't exist."""
    r = client.get("/bulk/export/nonexistent-job-id")
    assert r.status_code == 404


def test_export_completed_job():
    """Upload CSV, wait for completion, then export."""
    csv_content = b"review\nGreat product\nTerrible service\n"
    r = client.post(
        "/bulk",
        files={"file": ("test.csv", csv_content, "text/csv")},
    )
    assert r.status_code == 200
    job_id = r.json()["job_id"]

    # Wait for completion (max 30s)
    for _ in range(60):
        status = client.get(f"/bulk/status/{job_id}").json()
        if status["status"] == "completed":
            break
        time.sleep(0.5)
    else:
        raise AssertionError(
            f"Job did not complete: {status['status']}"
        )

    # Export
    r = client.get(f"/bulk/export/{job_id}")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    lines = r.text.strip().split("\n")
    assert lines[0].startswith("row_index")  # header row
    assert len(lines) >= 3  # header + 2 data rows
