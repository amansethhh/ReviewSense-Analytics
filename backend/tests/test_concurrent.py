"""
Phase 11 — Concurrency tests.

Tests thread-safety of _job_store, concurrent bulk jobs,
/bulk/active endpoint, and stale job eviction.
"""
import threading
import time
import uuid
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.routes.bulk import (
    _job_store,
    _store_lock,
    _append_log,
    cleanup_stale_jobs,
    BulkJobStatus,
)


client = TestClient(app)


# ── helpers ────────────────────────────────────────────────────────────────

def _make_job(status: str = "processing", age_minutes: int = 0) -> str:
    """Insert a synthetic job directly into _job_store."""
    job_id = str(uuid.uuid4())
    created = datetime.now(timezone.utc) - timedelta(minutes=age_minutes)
    with _store_lock:
        _job_store[job_id] = {
            "job_id":     job_id,
            "status":     BulkJobStatus(status),
            "progress":   0.0,
            "total_rows": 10,
            "processed":  0,
            "results":    None,
            "summary":    None,
            "error":      None,
            "logs":       [],
            "created_at": created,
            "page":       "bulk",
        }
    return job_id


def _remove_job(job_id: str) -> None:
    with _store_lock:
        _job_store.pop(job_id, None)


# ── test_job_store_thread_safety ───────────────────────────────────────────

def test_job_store_thread_safety():
    """
    Spawn 10 threads all calling _append_log on the same job_id
    simultaneously.  After all threads complete,
    len(logs) must be exactly 10 — no lost writes.
    """
    job_id = _make_job(status="processing")
    try:
        threads = [
            threading.Thread(
                target=_append_log,
                args=(job_id, f"log line {i}"),
            )
            for i in range(10)
        ]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        with _store_lock:
            log_count = len(_job_store[job_id]["logs"])

        assert log_count == 10, (
            f"Expected 10 log lines, got {log_count} — "
            "possible thread-unsafe write"
        )
    finally:
        _remove_job(job_id)


# ── test_active_jobs_endpoint ──────────────────────────────────────────────

def test_active_jobs_endpoint():
    """
    Insert a processing job → verify GET /bulk/active returns it.
    Mark completed → verify it no longer appears.
    """
    job_id = _make_job(status="processing")
    try:
        resp = client.get("/bulk/active")
        assert resp.status_code == 200
        data = resp.json()
        ids = [j["job_id"] for j in data["active_jobs"]]
        assert job_id in ids, (
            f"Job {job_id[:8]} should appear in active_jobs"
        )

        # Mark as completed
        with _store_lock:
            _job_store[job_id]["status"] = BulkJobStatus.completed

        resp2 = client.get("/bulk/active")
        assert resp2.status_code == 200
        data2 = resp2.json()
        ids2 = [j["job_id"] for j in data2["active_jobs"]]
        assert job_id not in ids2, (
            f"Completed job {job_id[:8]} must NOT appear in active_jobs"
        )
    finally:
        _remove_job(job_id)


# ── test_stale_job_eviction ────────────────────────────────────────────────

def test_stale_job_eviction():
    """
    Create a completed job aged 31 minutes (> 30-min TTL).
    Call cleanup_stale_jobs() directly.
    Verify the job is removed from _job_store.
    """
    job_id = _make_job(status="completed", age_minutes=31)
    try:
        with _store_lock:
            assert job_id in _job_store, "Job should exist before cleanup"

        evicted = cleanup_stale_jobs()
        assert evicted >= 1, f"Expected at least 1 eviction, got {evicted}"

        with _store_lock:
            assert job_id not in _job_store, (
                f"Stale job {job_id[:8]} should have been evicted"
            )
    finally:
        _remove_job(job_id)  # no-op if already evicted


# ── test_active_jobs_page_field ──────────────────────────────────────────

def test_active_jobs_page_field():
    """
    Insert one job with page='bulk' and one with page='language'.
    Verify GET /bulk/active returns the correct page field for each.
    """
    bulk_jid = _make_job(status="processing")
    lang_jid = _make_job(status="processing")
    try:
        # Override page field directly
        with _store_lock:
            _job_store[bulk_jid]["page"] = "bulk"
            _job_store[lang_jid]["page"] = "language"

        resp = client.get("/bulk/active")
        assert resp.status_code == 200
        jobs = {j["job_id"]: j for j in resp.json()["active_jobs"]}

        assert bulk_jid in jobs
        assert lang_jid in jobs
        assert jobs[bulk_jid]["page"] == "bulk"
        assert jobs[lang_jid]["page"] == "language"
    finally:
        _remove_job(bulk_jid)
        _remove_job(lang_jid)
