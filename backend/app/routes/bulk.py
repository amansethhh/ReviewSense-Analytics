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

from app.schemas import (
    BulkJobSubmitResponse, BulkJobResult,
    BulkJobStatus, BulkRowResult,
    ABSAItem, SentimentLabel,
)
from app.dependencies import (
    get_model, get_vectorizer, add_src_to_path
)
from app.config import get_settings
from app.utils import normalize_confidence
from app.adaptive import adaptive_batch_sizer
from app.cache import prediction_cache
from app.metrics_store import metrics_store

router = APIRouter()
logger = logging.getLogger("reviewsense.bulk")
add_src_to_path()

# ── In-memory job store ────────────────────────────────────
_job_store: dict[str, dict] = {}
_job_expiry: dict[str, datetime] = {}

# BUG-4 FIX: Thread-safe lock for all _job_store mutations
_store_lock = threading.Lock()

# OPT-4: Thread-safe lock for transformer model predictions
_model_lock = threading.Lock()

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


def _update_progress_pct(job_id: str, pct: float) -> None:
    """Thread-safe progress update — MONOTONICALLY INCREASING only.
    Prevents progress bar from going backwards when parallel futures
    complete out-of-order (Phase 1 detection race condition).
    """
    with _store_lock:
        if job_id in _job_store:
            current = _job_store[job_id].get("progress", 0.0)
            if pct > current:  # Never decrease — only advance
                _job_store[job_id]["progress"] = pct


def _update_progress(
    job_id: str, processed: int, total: int
) -> None:
    """Thread-safe progress update for Phase 3 (scales 40% -> 100%)."""
    with _store_lock:
        if job_id in _job_store:
            _job_store[job_id]["processed"] = processed
            base_pct = 40.0
            phase3_pct = (processed / total) * 60.0 if total > 0 else 0.0
            _job_store[job_id]["progress"] = base_pct + phase3_pct


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
    OPTIMIZED bulk analysis pipeline — 3-phase architecture.

    Phase 1: Language detection (fast, sequential)
    Phase 2: Batch translation (grouped by language)
    Phase 3: Parallel sentiment + ABSA + sarcasm

    All phases are fully synchronous — NO asyncio.
    Thread-safe via _model_lock for transformer predictions.
    """
    try:
        from src.predict import predict_sentiment
        # BUG-2 FIX: Use centralized language detection
        from app.utils.language_detection import (
            detect_language_robust,
            LANGUAGE_CODE_MAP,
        )
        from app.routes.language import (
            detect_language_adaptive,
            _apply_sentiment_corrections,
        )
        from app.cache import pipeline_cache

        total = len(df)
        results: list[BulkRowResult] = []
        processed_count = 0

        with _store_lock:
            _job_store[job_id]["status"] = BulkJobStatus.processing
            _job_store[job_id]["total_rows"] = total
            _job_store[job_id]["results"] = []
            _job_store[job_id]["phase"] = "init"

        # Extract all texts first
        all_texts: list[str] = []
        all_indices: list[int] = []
        valid_mask: list[bool] = []  # True if row has valid text

        for idx, (i, row) in enumerate(df.iterrows()):
            text = str(row[text_col]).strip()
            is_valid = bool(
                text and text.lower() not in ["nan", "none", ""]
            )
            all_texts.append(text if is_valid else "")
            all_indices.append(int(i))
            valid_mask.append(is_valid)

            if len(text) > 10000 and is_valid:
                all_texts[-1] = text[:10000]

        valid_count = sum(valid_mask)
        _append_log(
            job_id,
            f"[{_ts()}] Pipeline started -- "
            f"{total} rows ({valid_count} valid), "
            f"{_MAX_ROW_WORKERS} workers"
        )

        # ══════════════════════════════════════════════════
        # PHASE 1: Language Detection (fast, sequential)
        # ══════════════════════════════════════════════════
        detected_langs: list[str] = ["en"] * total
        lang_names: list[str] = ["English"] * total
        lang_confs: list[float] = [1.0] * total

        if multilingual:
            with _store_lock:
                _job_store[job_id]["phase"] = "detecting"

            _append_log(
                job_id,
                f"[{_ts()}] Phase 1: Detecting languages "
                f"for {valid_count} reviews (parallel)..."
            )

            # PERF FIX: Parallel language detection replaces serial loop
            # detect_language_adaptive is CPU-bound NLP (~5-15ms each)
            # Parallelizing across workers gives 3-4x speedup
            detect_completed = [0]  # mutable counter for progress

            def _detect_one(idx: int):
                if not valid_mask[idx]:
                    return idx, "en", 1.0
                try:
                    lc, lconf = detect_language_adaptive(all_texts[idx])
                    return idx, lc, lconf
                except Exception:
                    return idx, "en", 0.5

            with ThreadPoolExecutor(
                max_workers=_MAX_ROW_WORKERS,
                thread_name_prefix="bulk-detect",
            ) as det_executor:
                det_futures = [
                    det_executor.submit(_detect_one, i)
                    for i in range(total)
                ]
                from concurrent.futures import as_completed as _as_completed
                for det_future in _as_completed(det_futures):
                    idx, lc, lconf = det_future.result()
                    detected_langs[idx] = lc
                    lang_confs[idx] = lconf
                    lang_names[idx] = LANGUAGE_CODE_MAP.get(
                        lc, lc.title() if lc != "unknown" else "Unknown"
                    )
                    detect_completed[0] += 1
                    if detect_completed[0] % 10 == 0 or detect_completed[0] == total:
                        _update_progress_pct(
                            job_id,
                            detect_completed[0] / total * 15.0
                        )

            # Count languages for log
            from collections import Counter
            lang_counts = Counter(
                detected_langs[i] for i in range(total)
                if valid_mask[i]
            )
            en_count = lang_counts.get("en", 0)
            non_en = valid_count - en_count
            _append_log(
                job_id,
                f"[{_ts()}] Phase 1 complete: "
                f"{en_count} English, {non_en} non-English"
            )

        # ══════════════════════════════════════════════════
        # PHASE 2: Batch Translation (grouped by language)
        # ══════════════════════════════════════════════════
        translated_texts: list[str] = list(all_texts)  # copy
        trans_methods: list[str | None] = [None] * total
        was_translated: list[bool] = [False] * total

        if multilingual:
            with _store_lock:
                _job_store[job_id]["phase"] = "translating"

            _append_log(
                job_id,
                f"[{_ts()}] Phase 2: Batch translating "
                f"{non_en} non-English reviews (parallel)..."
            )

            # Group non-English reviews by language
            from collections import defaultdict
            lang_groups: dict[
                str, list[tuple[int, str]]
            ] = defaultdict(list)
            for idx in range(total):
                if not valid_mask[idx]:
                    continue
                lc = detected_langs[idx]
                if lc == "en" and lang_confs[idx] >= 0.85:
                    trans_methods[idx] = "none"
                    continue
                lang_groups[lc].append((idx, all_texts[idx]))

            # PERF FIX: Translate all language groups IN PARALLEL
            # Each language group is an independent Google Translate batch
            # No dependency between groups → run concurrently
            from app.utils.batch_translate import translate_batch_for_lang
            translate_lock = threading.Lock()
            translate_done = [0]

            def _translate_lang_group(
                lang: str,
                indexed_texts: list,
            ) -> None:
                indices = [i for i, _ in indexed_texts]
                texts   = [t for _, t in indexed_texts]
                try:
                    batch_results = translate_batch_for_lang(texts, lang)
                    with translate_lock:
                        for idx, result in zip(indices, batch_results):
                            translated_texts[idx] = result
                            trans_methods[idx] = "google_batch"
                            was_translated[idx] = True
                            translate_done[0] += 1
                except Exception as e:
                    logger.warning(
                        f"Batch translation failed for {lang}: {e}"
                    )
                    with translate_lock:
                        for idx, text in zip(indices, texts):
                            translated_texts[idx] = text
                            trans_methods[idx] = "failed"
                            translate_done[0] += 1
                # Update progress (15% → 40%)
                pct_done = translate_done[0] / max(1, non_en)
                _update_progress_pct(job_id, 15.0 + 25.0 * pct_done)

            with ThreadPoolExecutor(
                max_workers=min(4, len(lang_groups) or 1),
                thread_name_prefix="bulk-translate",
            ) as trans_executor:
                trans_futures = [
                    trans_executor.submit(
                        _translate_lang_group, lang, indexed_texts
                    )
                    for lang, indexed_texts in lang_groups.items()
                ]
                # Wait for all translation groups to finish
                for f in trans_futures:
                    try:
                        f.result(timeout=120.0)
                    except Exception as e:
                        logger.warning(f"Translation group failed: {e}")


            _append_log(
                job_id,
                f"[{_ts()}] Phase 2 complete: "
                f"batch translation done"
            )

        # ══════════════════════════════════════════════════
        # PHASE 3: BATCH Sentiment + Post-Processing
        # ══════════════════════════════════════════════════
        # PERF FIX: Vectorized batch inference replaces
        # per-row _model_lock serialization (10-30x faster).
        with _store_lock:
            _job_store[job_id]["phase"] = "analyzing"

        _append_log(
            job_id,
            f"[{_ts()}] Phase 3: Batch sentiment analysis "
            f"(vectorized, {total} reviews)..."
        )

        # 3A: Prepare texts for batch inference
        # CRITICAL: Classify on ORIGINAL text, not translated.
        # Translation is for display only. The XLM model handles
        # non-Latin scripts natively.
        predict_texts: list[str] = []
        predict_lang_codes: list[str] = []
        for idx in range(total):
            if not valid_mask[idx]:
                predict_texts.append("empty")
            else:
                predict_texts.append(
                    all_texts[idx] or "empty"
                )
            predict_lang_codes.append(
                detected_langs[idx]
            )

        # 3B: Run BATCH sentiment with language routing
        # (XLM-RoBERTa for non-Latin, English RoBERTa for Latin)
        from src.models.sentiment import (
            predict_batch as _sentiment_batch,
        )
        _update_progress_pct(job_id, 42.0)

        batch_predictions = _sentiment_batch(
            predict_texts,
            lang_codes=predict_lang_codes,
            batch_size=32,
        )

        _update_progress_pct(job_id, 65.0)
        _append_log(
            job_id,
            f"[{_ts()}] Phase 3: Batch inference complete "
            f"({len(batch_predictions)} predictions)"
        )

        # 3C: Per-row polarity computed inside _postprocess_row
        # (parallelized — was a serial O(n) blocking loop here)
        _update_progress_pct(job_id, 68.0)

        completed = 0

        def _postprocess_row(
            row_idx: int,
        ) -> BulkRowResult:
            """Post-process one row (corrections, ABSA,
            sarcasm). No model lock needed."""
            original_text = all_texts[row_idx]
            lang_code = detected_langs[row_idx]
            lang_name = lang_names[row_idx]
            det_method = trans_methods[row_idx]
            eng_text = translated_texts[row_idx]
            predict_text = predict_texts[row_idx]

            if not valid_mask[row_idx]:
                return BulkRowResult(
                    row_index=all_indices[row_idx],
                    text="",
                    sentiment=SentimentLabel("unknown"),
                    confidence=0.0,
                    polarity=0.0,
                    subjectivity=0.0,
                )

            # OPT-5: Pipeline cache check
            cached = pipeline_cache.get(
                original_text, lang_code
            )
            if cached is not None:
                return BulkRowResult(
                    row_index=all_indices[row_idx],
                    **cached,
                )

            # Use batch prediction result
            pred = batch_predictions[row_idx]
            label_name = pred.get(
                "label_name", "Neutral"
            )
            sentiment_raw = label_name.lower()
            if sentiment_raw not in [
                "positive", "negative", "neutral"
            ]:
                sentiment_raw = "neutral"

            raw_conf = float(
                pred.get("confidence", 0.0)
            )
            confidence_pct = normalize_confidence(
                raw_conf
            )
            # FIX-2: VADER + TextBlob dual polarity
            try:
                from src.predict import (
                    compute_dual_polarity,
                )
                polarity_val, vader_compound, subjectivity_val = (
                    compute_dual_polarity(
                        predict_text, lang_code
                    )
                )
            except Exception:
                polarity_val = 0.0
                vader_compound = 0.0
                subjectivity_val = 0.0

            # Apply sentiment corrections
            sentiment_raw, confidence_pct, polarity_val = (
                _apply_sentiment_corrections(
                    predict_text,
                    sentiment_raw,
                    confidence_pct,
                    polarity_val,
                )
            )

            # OPT-2: Conditional ABSA
            absa_list = None
            if run_absa:
                words = predict_text.split()
                if (len(words) >= 5
                        and confidence_pct < 97.0):
                    absa_list = _run_absa_sync(
                        predict_text
                    )

            # Sarcasm
            sarcasm_detected = None
            if run_sarcasm:
                sarcasm_detected = _run_sarcasm_sync(
                    predict_text
                )

            row_result_dict = {
                "text": original_text[:500],
                "sentiment": SentimentLabel(
                    sentiment_raw
                ),
                "confidence": confidence_pct,
                "polarity": polarity_val,
                "subjectivity": float(subjectivity_val),
                "sarcasm_detected": sarcasm_detected,
                "aspects": absa_list,
                "detected_language": (
                    lang_name if multilingual
                    else None
                ),
                "translation_method": det_method,
                "translated_text": (
                    eng_text
                    if was_translated[row_idx]
                    else None
                ),
            }

            # OPT-5: Cache the result
            pipeline_cache.set(
                original_text, lang_code,
                row_result_dict,
            )

            return BulkRowResult(
                row_index=all_indices[row_idx],
                **row_result_dict,
            )

        # Execute post-processing in parallel
        # FIX-4+5: Single lock per row; no redundant local results list
        from concurrent.futures import as_completed

        with ThreadPoolExecutor(
            max_workers=_MAX_ROW_WORKERS,
            thread_name_prefix="bulk-postproc",
        ) as executor:
            future_to_idx = {
                executor.submit(
                    _postprocess_row, idx
                ): idx
                for idx in range(total)
            }

            for future in as_completed(future_to_idx):
                idx = future_to_idx[future]
                try:
                    row_result = future.result(
                        timeout=_ROW_TIMEOUT_S
                    )
                except FuturesTimeoutError:
                    metrics_store.record_timeout()
                    row_result = BulkRowResult(
                        row_index=all_indices[idx],
                        text=all_texts[idx][:500],
                        sentiment=SentimentLabel(
                            "unknown"
                        ),
                        confidence=0.0,
                        polarity=0.0,
                        subjectivity=0.0,
                        detected_language=(
                            lang_names[idx]
                            if multilingual else None
                        ),
                        translation_method="timeout",
                    )
                except Exception:
                    row_result = BulkRowResult(
                        row_index=all_indices[idx],
                        text=all_texts[idx][:500],
                        sentiment=SentimentLabel(
                            "unknown"
                        ),
                        confidence=0.0,
                        polarity=0.0,
                        subjectivity=0.0,
                    )

                completed += 1
                row_dict = row_result.model_dump()
                pct = 68.0 + (completed / total) * 32.0
                should_log = (
                    completed % 10 == 0
                    or completed == total
                )

                # FIX-4: Single lock acquire for append+progress+log
                with _store_lock:
                    if job_id in _job_store:
                        _job_store[job_id][
                            "results"
                        ].append(row_dict)
                        _job_store[job_id][
                            "progress"
                        ] = pct
                        _job_store[job_id][
                            "processed"
                        ] = completed
                        if should_log:
                            log_pct = int(
                                (completed / total) * 100
                            )
                            _job_store[job_id][
                                "logs"
                            ].append(
                                f"[{_ts()}] Phase 3: "
                                f"{completed}/{total} "
                                f"({log_pct}%) post-processed"
                            )

                # Metrics outside lock (non-blocking)
                if row_result.sentiment.value != "unknown":
                    metrics_store.record_prediction(
                        row_result.sentiment.value,
                        row_result.detected_language,
                    )


        # ── Build summary ──────────────────────────────────
        # FIX-5: Read from job store (no redundant local results list)
        with _store_lock:
            final_results = list(
                _job_store[job_id].get("results", [])
            )
        n = len(final_results)
        sentiments = [
            r.get("sentiment", "neutral")
            for r in final_results
        ]
        pos = sentiments.count("positive")
        neg = sentiments.count("negative")
        neu = sentiments.count("neutral")

        summary = {
            "total_analyzed": n,
            "positive": pos,
            "negative": neg,
            "neutral":  neu,
            "positive_pct": round(
                pos / n * 100, 1
            ) if n else 0,
            "negative_pct": round(
                neg / n * 100, 1
            ) if n else 0,
            "neutral_pct": round(
                neu / n * 100, 1
            ) if n else 0,
            "sarcasm_count": sum(
                1 for r in final_results
                if r.get("sarcasm_detected")
            ),
        }

        _append_log(
            job_id,
            f"[{_ts()}] Analysis complete -- "
            f"{n} reviews processed"
        )

        with _store_lock:
            _job_store[job_id].update({
                "status":    BulkJobStatus.completed,
                "progress":  100.0,
                "processed": n,
                # results already accumulated as dicts in job store
                "summary":   summary,
                "phase":     "done",
            })
        logger.info(
            f"Job {job_id[:8]} complete: "
            f"{n} rows processed"
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
            f"[{_ts()}] FATAL ERROR: {str(e)[:200]}"
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

    # FIX-2: Cap results payload during processing to prevent 500ms poll
    # from sending growing MB-sized JSON arrays. Full results only at completion.
    all_results = job.get("results") or []
    status_val  = job.get("status")
    is_done = status_val in (
        BulkJobStatus.completed,
        BulkJobStatus.completed.value,
        "completed",
    )
    # Build live sentiment counts from ALL accumulated results
    # (not the capped 50 window — gives accurate real-time totals for live panels)
    live_pos     = sum(1 for r in all_results if r.get('sentiment') == 'positive')
    live_neg     = sum(1 for r in all_results if r.get('sentiment') == 'negative')
    live_neu     = sum(1 for r in all_results if r.get('sentiment') == 'neutral')
    live_sarcasm = sum(1 for r in all_results if r.get('sarcasm_detected'))

    # FIX-2: Cap results payload — last 50 during processing, full at completion
    if is_done:
        streamed_results = all_results if all_results else None
    elif all_results:
        streamed_results = all_results[-50:]
    else:
        streamed_results = None

    return BulkJobResult(**{
        **job,
        "results": streamed_results,
        "live_pos": live_pos,
        "live_neg": live_neg,
        "live_neu": live_neu,
        "live_sarcasm": live_sarcasm,
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
