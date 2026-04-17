# CRITICAL DESIGN:
# Render free tier has a 30-second HTTP timeout.
# A 1000-row CSV with full ML analysis takes minutes.
# Solution: daemon Thread + in-memory job store + polling.
# React frontend polls GET /bulk/status/{job_id} every 500ms.
#
# BUG-2 FIX: Fully synchronous _process_bulk_job(). No asyncio.
# BUG-4 FIX: Thread-safe _store_lock for all _job_store mutations.
# BUG-5 FIX: Per-row timeout 15s. Never skip rows — record errors.

import io
import uuid
import time
import logging
import threading
from typing import Any
from datetime import datetime, timedelta, timezone
from concurrent.futures import (
    ThreadPoolExecutor,
    TimeoutError as FuturesTimeoutError,
)

import pandas as pd
from fastapi import (
    APIRouter, Depends, HTTPException,
    UploadFile, File, Form, Query,
)
from fastapi.responses import StreamingResponse

from backend.app.schemas import (
    BulkJobSubmitResponse, BulkJobResult,
    BulkJobStatus, BulkRowResult,
    ABSAItem, SentimentLabel,
)
from backend.app.dependencies import (
    get_model, get_vectorizer, add_src_to_path
)
from backend.app.config import get_settings
from backend.app.utils import normalize_confidence
from backend.app.adaptive import adaptive_batch_sizer
from backend.app.cache import prediction_cache
from backend.app.metrics_store import metrics_store

router = APIRouter()
logger = logging.getLogger("reviewsense.bulk")
add_src_to_path()

# ── In-memory job store ────────────────────────────────────
_job_store: dict[str, dict] = {}
_job_expiry: dict[str, datetime] = {}

# BUG-4 FIX: Thread-safe lock for all _job_store mutations
_store_lock = threading.Lock()

# O8: Stale job expiry interval (seconds)
_STALE_JOB_AGE_SECONDS: int = 1800  # 30 minutes

# BUG-5 FIX: Increased from 5s → 15s for multilingual safety
_ROW_TIMEOUT_S: float = 15.0

# Performance: Scale workers based on CPU cores
import multiprocessing as _mp
_MAX_ROW_WORKERS = min(4, _mp.cpu_count() or 2)

# Dedicated executor for per-row timeout isolation.
_row_executor = ThreadPoolExecutor(
    max_workers=_MAX_ROW_WORKERS,
    thread_name_prefix="bulk-row-timeout",
)


def _ts() -> str:
    """Timestamp helper for log lines (HH:MM:SS)."""
    return datetime.now().strftime("%H:%M:%S")


# ── BUG-4 FIX: Thread-safe helpers ────────────────────────

def _append_log(job_id: str, message: str) -> None:
    """Thread-safe log append to _job_store."""
    with _store_lock:
        if job_id in _job_store:
            _job_store[job_id]["logs"].append(message)


def _update_progress(
    job_id: str, processed: int, total: int
) -> None:
    """Thread-safe progress update."""
    with _store_lock:
        if job_id in _job_store:
            _job_store[job_id]["processed"] = processed
            _job_store[job_id]["progress"] = (
                (processed / total) * 100
                if total > 0 else 0.0
            )


def _cleanup_expired_jobs():
    """Remove jobs older than TTL."""
    now = datetime.now(timezone.utc)
    expired = [
        jid for jid, exp in _job_expiry.items()
        if now > exp
    ]
    for jid in expired:
        _job_store.pop(jid, None)
        _job_expiry.pop(jid, None)


def cleanup_stale_jobs() -> int:
    """
    O8: Remove completed/failed jobs older than 30 minutes.
    Active jobs (status=processing/queued) are NEVER evicted.
    """
    now = datetime.now(timezone.utc)
    stale_ids = []

    for jid, job in _job_store.items():
        created_at = job.get("created_at")
        if created_at is None:
            continue
        status = job.get("status")
        if status in (BulkJobStatus.queued,
                      BulkJobStatus.processing):
            continue
        age_seconds = (now - created_at).total_seconds()
        if age_seconds > _STALE_JOB_AGE_SECONDS:
            stale_ids.append(jid)

    for jid in stale_ids:
        _job_store.pop(jid, None)
        _job_expiry.pop(jid, None)
        logger.debug(f"Evicted stale job {jid[:8]}")

    return len(stale_ids)


def _process_bulk_job(
    job_id: str,
    df: pd.DataFrame,
    text_col: str,
    model_choice: str,
    run_absa: bool,
    run_sarcasm: bool,
    model: Any,
    vectorizer: Any,
    multilingual: bool = False,
):
    """
    FULLY SYNCHRONOUS bulk analysis pipeline.
    Runs in a daemon thread — NEVER touches asyncio.

    BUG-2 FIX: No asyncio.run(), await, or event loop calls.
    BUG-4 FIX: All _job_store mutations use _store_lock.
    BUG-5 FIX: 15s per-row timeout. Never skips rows —
               records them with error info instead.

    Uses detect_translate_and_predict_sync() from language.py
    for correct translation-first, cache-second ordering.
    """
    try:
        # Import the synchronous prediction helper
        from backend.app.routes.language import (
            detect_translate_and_predict_sync,
        )

        total = len(df)
        results: list[BulkRowResult] = []
        processed_count = 0

        with _store_lock:
            _job_store[job_id]["status"] = (
                BulkJobStatus.processing)
            _job_store[job_id]["total_rows"] = total
            _job_store[job_id]["results"] = []  # init for streaming

        _append_log(
            job_id,
            f"[{_ts()}] Pipeline started — "
            f"{total} rows, {_MAX_ROW_WORKERS} workers"
        )

        for idx, (i, row) in enumerate(df.iterrows()):
            row_num = idx + 1
            try:
                text = str(row[text_col]).strip()
                if not text or text.lower() in [
                    "nan", "none", ""
                ]:
                    # B5: Record empty rows with unknown
                    results.append(BulkRowResult(
                        row_index=int(i),
                        text="",
                        sentiment=SentimentLabel("unknown"),
                        confidence=0.0,
                        polarity=0.0,
                        subjectivity=0.0,
                    ))
                    processed_count += 1
                    _update_progress(
                        job_id, processed_count, total)
                    _append_log(
                        job_id,
                        f"[{_ts()}] Row {row_num}/{total}:"
                        f" SKIPPED -- empty row"
                    )
                    continue

                # B5: Truncate oversized text
                if len(text) > 10000:
                    text = text[:10000]
                    _append_log(
                        job_id,
                        f"[{_ts()}] Row {row_num}/{total}:"
                        f" TEXT TRUNCATED to 10,000 chars"
                    )

                # ── Per-row prediction with timeout ──────
                try:
                    future = _row_executor.submit(
                        detect_translate_and_predict_sync,
                        text,
                        model_choice,
                        multilingual,
                        run_absa,
                        run_sarcasm,
                    )
                    pred_result = future.result(
                        timeout=_ROW_TIMEOUT_S)
                except FuturesTimeoutError:
                    # BUG-5 FIX: Never skip — record with
                    # error instead
                    metrics_store.record_timeout()
                    logger.warning(
                        f"Row {row_num}: timeout after "
                        f"{_ROW_TIMEOUT_S}s"
                    )
                    _append_log(
                        job_id,
                        f"[{_ts()}] Row {row_num}/{total}:"
                        f" TIMEOUT after {_ROW_TIMEOUT_S}s"
                        f" — marked unknown"
                    )
                    # Still detect language for metadata
                    to_lang = None
                    to_method = None
                    if multilingual:
                        try:
                            from backend.app.routes.language import detect_language_adaptive, LANGUAGE_CODE_MAP
                            lc, _ = detect_language_adaptive(text)
                            to_lang = LANGUAGE_CODE_MAP.get(lc, lc.title() if lc != 'unknown' else None)
                            to_method = 'timeout'
                        except Exception:
                            pass
                    results.append(BulkRowResult(
                        row_index=int(i),
                        text=text[:500],
                        sentiment=SentimentLabel("unknown"),
                        confidence=0.0,
                        polarity=0.0,
                        subjectivity=0.0,
                        detected_language=to_lang,
                        translation_method=to_method,
                    ))
                    processed_count += 1
                    _update_progress(
                        job_id, processed_count, total)
                    continue
                except Exception as e:
                    logger.warning(
                        f"Row {row_num}: prediction "
                        f"failed: {e}"
                    )
                    _append_log(
                        job_id,
                        f"[{_ts()}] Row {row_num}/{total}:"
                        f" ERROR — {str(e)[:60]}"
                    )
                    # Still detect language for metadata
                    er_lang = None
                    er_method = None
                    if multilingual:
                        try:
                            from backend.app.routes.language import detect_language_adaptive, LANGUAGE_CODE_MAP
                            lc, _ = detect_language_adaptive(text)
                            er_lang = LANGUAGE_CODE_MAP.get(lc, lc.title() if lc != 'unknown' else None)
                            er_method = 'error'
                        except Exception:
                            pass
                    results.append(BulkRowResult(
                        row_index=int(i),
                        text=text[:500],
                        sentiment=SentimentLabel("unknown"),
                        confidence=0.0,
                        polarity=0.0,
                        subjectivity=0.0,
                        detected_language=er_lang,
                        translation_method=er_method,
                    ))
                    processed_count += 1
                    _update_progress(
                        job_id, processed_count, total)
                    continue

                # ── Extract prediction result ────────────
                sentiment_raw = pred_result.get(
                    "sentiment", "neutral")
                if sentiment_raw not in [
                    "positive", "negative", "neutral", "unknown"
                ]:
                    sentiment_raw = "neutral"

                confidence_pct = float(
                    pred_result.get("confidence", 0.0))
                cache_hit = pred_result.get(
                    "cache_hit", False)

                # Optional ABSA (with timeout)
                absa_list = None
                if run_absa:
                    try:
                        absa_future = _row_executor.submit(
                            _run_absa_sync, text
                        )
                        absa_list = absa_future.result(
                            timeout=_ROW_TIMEOUT_S
                        )
                    except (FuturesTimeoutError, Exception):
                        absa_list = None

                # Optional sarcasm (with timeout)
                sarcasm_detected = None
                if run_sarcasm:
                    try:
                        sar_future = _row_executor.submit(
                            _run_sarcasm_sync, text
                        )
                        sarcasm_detected = (
                            sar_future.result(
                                timeout=_ROW_TIMEOUT_S
                            )
                        )
                    except (FuturesTimeoutError, Exception):
                        sarcasm_detected = None

                # Extract language metadata when multilingual
                det_lang = None
                trans_method = None
                trans_text = None
                if multilingual:
                    det_lang = pred_result.get(
                        "detected_language", None)
                    trans_method = pred_result.get(
                        "translation_method", None)
                    trans_text = pred_result.get(
                        "translated_text", None)

                row_result = BulkRowResult(
                    row_index=int(i),
                    text=text[:500],
                    sentiment=SentimentLabel(sentiment_raw),
                    confidence=confidence_pct,
                    polarity=float(
                        pred_result.get("polarity", 0.0)),
                    subjectivity=float(
                        pred_result.get(
                            "subjectivity", 0.0)),
                    sarcasm_detected=sarcasm_detected,
                    aspects=absa_list,
                    detected_language=det_lang,
                    translation_method=trans_method,
                    translated_text=trans_text,
                )
                results.append(row_result)
                processed_count += 1

                # Stream result to job store for real-time panels
                with _store_lock:
                    if job_id in _job_store:
                        _job_store[job_id]["results"].append(
                            row_result.model_dump())

                # Record prediction for live dashboard stats
                metrics_store.record_prediction(
                    sentiment_raw, det_lang)

                # Thread-safe progress update
                _update_progress(
                    job_id, processed_count, total)

                # Per-row log
                hit_str = " [cached]" if cache_hit else ""
                lang_str = (
                    f" | lang={det_lang}"
                    f" via {trans_method}"
                ) if multilingual and det_lang else ""
                _append_log(
                    job_id,
                    f"[{_ts()}] Row {row_num}/{total}: "
                    f"{sentiment_raw} "
                    f"({confidence_pct:.1f}%){hit_str}"
                    f"{lang_str}"
                )

                # Milestone log every 10 rows
                if row_num % 10 == 0:
                    pct = int(
                        (processed_count / total) * 100)
                    _append_log(
                        job_id,
                        f"[{_ts()}] ── Milestone: "
                        f"{row_num}/{total} ({pct}%) ──"
                    )

                # O9: Smart throttling
                if adaptive_batch_sizer.should_throttle():
                    time.sleep(0.1)

            except Exception as e:
                logger.warning(
                    f"Row {row_num} failed: {e}")
                _append_log(
                    job_id,
                    f"[{_ts()}] Row {row_num}/{total}: "
                    f"failed — {str(e)[:60]}"
                )
                # BUG-5 FIX: Record failure, don't skip
                results.append(BulkRowResult(
                    row_index=int(i),
                    text=str(row.get(text_col, ""))[:500],
                    sentiment=SentimentLabel("unknown"),
                    confidence=0.0,
                    polarity=0.0,
                    subjectivity=0.0,
                ))
                processed_count += 1
                _update_progress(
                    job_id, processed_count, total)
                continue

        # ── Build summary ──────────────────────────────────
        sentiments = [r.sentiment.value for r in results]
        pos = sentiments.count("positive")
        neg = sentiments.count("negative")
        neu = sentiments.count("neutral")

        summary = {
            "total_analyzed": len(results),
            "positive": pos,
            "negative": neg,
            "neutral":  neu,
            "positive_pct": round(
                pos / len(results) * 100, 1)
                if results else 0,
            "negative_pct": round(
                neg / len(results) * 100, 1)
                if results else 0,
            "neutral_pct":  round(
                neu / len(results) * 100, 1)
                if results else 0,
            "sarcasm_count": sum(
                1 for r in results
                if r.sarcasm_detected
            ),
        }

        _append_log(
            job_id,
            f"[{_ts()}] ✓ Analysis complete — "
            f"{len(results)} reviews processed"
        )

        with _store_lock:
            _job_store[job_id].update({
                "status":    BulkJobStatus.completed,
                "progress":  100.0,
                "processed": len(results),
                "results":   [r.model_dump()
                              for r in results],
                "summary":   summary,
            })
        logger.info(
            f"Job {job_id[:8]} complete: "
            f"{len(results)} rows processed"
        )

    except Exception as e:
        logger.error(
            f"Job {job_id[:8]} FATAL: {e}",
            exc_info=True,
        )
        with _store_lock:
            if job_id in _job_store:
                _job_store[job_id]["status"] = (
                    BulkJobStatus.failed)
                _job_store[job_id]["error"] = str(e)
        _append_log(
            job_id,
            f"[{_ts()}] ✗ FATAL ERROR: {str(e)[:200]}"
        )


def _run_absa_sync(text: str) -> list[ABSAItem] | None:
    """
    Synchronous ABSA helper for per-row timeout executor.
    Returns list of ABSAItem or None.
    """
    try:
        from src.models.aspect import analyze_aspects
        raw = analyze_aspects(text)
        absa_list = []
        for item in (raw or []):
            if isinstance(item, dict):
                sv = str(item.get(
                    "sentiment_label",
                    item.get("sentiment", "Neutral")
                )).lower()
                if sv not in ["positive", "negative",
                              "neutral"]:
                    sv = "neutral"
                absa_list.append(ABSAItem(
                    aspect=item.get("aspect", ""),
                    sentiment=SentimentLabel(sv),
                    polarity=float(
                        item.get("polarity", 0)),
                    subjectivity=float(
                        item.get("subjectivity", 0.5)),
                ))
        return absa_list if absa_list else None
    except Exception:
        return None


def _run_sarcasm_sync(text: str) -> bool | None:
    """
    Synchronous sarcasm helper for per-row timeout executor.
    Returns is_sarcastic bool or None.
    """
    try:
        from src.sarcasm_detector import detect_sarcasm
        sr = detect_sarcasm(text)
        if isinstance(sr, dict):
            return sr.get("is_sarcastic", False)
        elif isinstance(sr, bool):
            return sr
        return None
    except Exception:
        return None


@router.post(
    "",
    response_model=BulkJobSubmitResponse,
    summary="Submit CSV for bulk sentiment analysis",
)
async def submit_bulk(
    file: UploadFile = File(...),
    text_column: str = Form("review"),
    model: str = Form("best"),
    run_absa: bool = Form(False),
    run_sarcasm: bool = Form(False),
    multilingual: bool = Form(False),
    page: str = Query("bulk", description="Originating page: 'bulk' or 'language'"),
    ml_model=Depends(get_model),
    vectorizer=Depends(get_vectorizer),
):
    _cleanup_expired_jobs()
    settings = get_settings()

    # ── Parse uploaded file ────────────────────────────────
    try:
        content = await file.read()
        filename = file.filename or "upload.csv"
        if filename.endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(content))
        else:
            df = pd.read_csv(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not parse file: {str(e)}"
        )

    # ── Validate ───────────────────────────────────────────
    if len(df) == 0:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file contains no rows."
        )
    if len(df) > settings.max_bulk_rows:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds max rows "
                   f"({settings.max_bulk_rows}). "
                   f"Got {len(df)} rows."
        )

    # Auto-detect text column if not found
    if text_column not in df.columns:
        candidates = ["review", "text", "Review", "Text",
                      "review_text", "comment", "Comment",
                      "content", "Content"]
        found = next(
            (c for c in candidates if c in df.columns),
            None
        )
        if found:
            text_column = found
            logger.info(
                f"Auto-detected text column: {text_column}"
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Column '{text_column}' not found. "
                    f"Available columns: "
                    f"{list(df.columns)}"
                )
            )

    # ── Create job ─────────────────────────────────────────
    job_id = str(uuid.uuid4())
    estimated = max(5, len(df) // 10)

    with _store_lock:
        _job_store[job_id] = {
            "job_id":     job_id,
            "status":     BulkJobStatus.queued,
            "progress":   0.0,
            "total_rows": len(df),
            "processed":  0,
            "results":    None,
            "summary":    None,
            "error":      None,
            "logs":       [
                f"[{_ts()}] Job {job_id[:8]} queued, "
                f"starting pipeline..."
            ],
            "created_at": datetime.now(timezone.utc),
            "page":       page if page in ("bulk", "language") else "bulk",
        }
    _job_expiry[job_id] = (
        datetime.now(timezone.utc) +
        timedelta(seconds=settings.job_ttl)
    )

    # ── Launch as daemon thread ────────────────────────────
    try:
        t = threading.Thread(
            target=_process_bulk_job,
            args=(
                job_id, df, text_column, model,
                run_absa, run_sarcasm,
                ml_model, vectorizer,
                multilingual,
            ),
            daemon=True,
            name=f"bulk-job-{job_id[:8]}",
        )
        t.start()
    except Exception as e:
        with _store_lock:
            _job_store[job_id]["status"] = (
                BulkJobStatus.failed)
            _job_store[job_id]["error"] = str(e)
        _append_log(
            job_id, f"[{_ts()}] ✗ Failed to start: {e}")
        logger.error(
            f"Failed to start thread for "
            f"{job_id[:8]}: {e}"
        )

    logger.info(
        f"Bulk job {job_id[:8]} queued: "
        f"{len(df)} rows, col={text_column}"
    )

    return BulkJobSubmitResponse(
        job_id=job_id,
        status=BulkJobStatus.queued,
        total_rows=len(df),
        estimated_seconds=estimated,
        poll_url=f"/bulk/status/{job_id}",
    )


@router.get(
    "/status/{job_id}",
    response_model=BulkJobResult,
    summary="Poll bulk job status and results",
)
async def get_bulk_status(job_id: str):
    if job_id not in _job_store:
        raise HTTPException(
            status_code=404,
            detail=f"Job {job_id} not found "
                   f"(may have expired or never existed)"
        )
    # BUG-4 FIX: Thread-safe read via shallow copy
    with _store_lock:
        job = dict(_job_store[job_id])
        # Copy logs list to prevent mutation during
        # serialization
        job["logs"] = list(job.get("logs", []))

    # Return results during both processing AND completed
    # so the frontend panels update in real-time
    return BulkJobResult(**{
        **job,
        "results": job["results"] if job["results"] else None,
    })


@router.get(
    "/columns",
    summary="Preview CSV columns before submitting bulk job",
)
async def preview_columns(file: UploadFile = File(...)):
    """
    Allows frontend to call this first to show the user
    which column to select as the review text column.
    """
    try:
        content = await file.read()
        filename = file.filename or "upload.csv"
        if filename.endswith(".xlsx"):
            df = pd.read_excel(io.BytesIO(content),
                               nrows=5)
        else:
            df = pd.read_csv(io.BytesIO(content), nrows=5)
        return {
            "columns": list(df.columns),
            "preview": df.head(3).to_dict(orient="records"),
            "total_rows_estimate": len(df),
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Could not parse file: {str(e)}"
        )


@router.get(
    "/export/{job_id}",
    summary="Download completed bulk job results as CSV",
)
async def export_bulk_results(job_id: str):
    """B3: Export completed bulk results as downloadable CSV."""
    import csv as csv_mod

    if job_id not in _job_store:
        raise HTTPException(
            status_code=404,
            detail="Job not found"
        )

    with _store_lock:
        job = dict(_job_store[job_id])

    if job["status"] != BulkJobStatus.completed.value:
        raise HTTPException(
            status_code=400,
            detail="Job not completed yet"
        )

    results = job.get("results", []) or []

    buf = io.StringIO()
    fieldnames = [
        "row_index", "text", "sentiment", "confidence",
        "polarity", "subjectivity", "detected_language",
        "translation_method", "translated_text",
        "sarcasm_detected",
    ]
    writer = csv_mod.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for r in results:
        writer.writerow({
            "row_index": r.get("row_index", ""),
            "text": r.get("text", ""),
            "sentiment": r.get("sentiment", ""),
            "confidence": r.get("confidence", ""),
            "polarity": r.get("polarity", ""),
            "subjectivity": r.get("subjectivity", ""),
            "detected_language": r.get(
                "detected_language", ""),
            "translation_method": r.get(
                "translation_method", ""),
            "translated_text": r.get(
                "translated_text", ""),
            "sarcasm_detected": r.get(
                "sarcasm_detected", ""),
        })

    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={
            "Content-Disposition": (
                f"attachment; filename="
                f"reviewsense_{job_id[:8]}.csv"
            )
        }
    )


@router.get("/jobs/count", summary="Job store memory stats")
async def get_job_count():
    """H1: Returns job store stats for production memory monitoring."""
    now = datetime.now(timezone.utc)
    with _store_lock:
        active = sum(
            1 for j in _job_store.values()
            if j.get("status") in (
                BulkJobStatus.queued,
                BulkJobStatus.processing,
            )
        )
        oldest_age = 0.0
        for j in _job_store.values():
            created = j.get("created_at")
            if created:
                age = (now - created).total_seconds()
                if age > oldest_age:
                    oldest_age = age
        return {
            "active_jobs": active,
            "total_in_memory": len(_job_store),
            "oldest_job_age_seconds": round(oldest_age, 1),
        }


@router.get("/active", summary="List all active (queued/processing) bulk jobs")
async def get_active_jobs():
    """
    Returns all jobs currently queued or processing.
    Used by the frontend nav bar active-jobs indicator.
    Completed and failed jobs are excluded.
    """
    active = []
    with _store_lock:
        for job in _job_store.values():
            status = job.get("status")
            if status not in (
                BulkJobStatus.queued,
                BulkJobStatus.processing,
            ):
                continue
            created = job.get("created_at")
            active.append({
                "job_id":     job["job_id"],
                "page":       job.get("page", "bulk"),
                "status":     status.value if hasattr(status, "value") else str(status),
                "processed":  job.get("processed", 0),
                "total":      job.get("total_rows", 0),
                "created_at": created.isoformat() if created else "",
            })
    return {"active_jobs": active}
