import time
import logging
import asyncio
from typing import Any
from fastapi import APIRouter, Depends, HTTPException

from app.schemas import (
    PredictRequest, PredictResponse,
    LIMEFeature, ABSAItem, SarcasmResult,
    SentimentLabel,
)
from app.dependencies import (
    get_model, get_vectorizer, add_src_to_path
)
from app.utils import normalize_confidence
from app.adaptive import (
    primary_pool,
    inference_throttler,
    request_deduplicator,
)
from app.cache import prediction_cache
from app.metrics_store import metrics_store

router = APIRouter()
logger = logging.getLogger("reviewsense.predict")
add_src_to_path()

# Phase 2, Part 4: Inference timeout (seconds)
_INFERENCE_TIMEOUT_S: float = 8.0


def _run_prediction(text: str, model_choice: str,
                    model: Any, vectorizer: Any) -> dict:
    """
    Runs in ThreadPoolExecutor to avoid blocking the
    async event loop during CPU-bound ML inference.
    Imports directly from src — DO NOT rewrite logic.

    src.predict.predict_sentiment returns:
      label (int), label_name (str), confidence (float 0-1),
      polarity (float), subjectivity (float)

    We also grab scores from src.models.sentiment.predict
    for the full 3-class probability distribution.
    """
    from src.predict import predict_sentiment

    result = predict_sentiment(text, model_choice)

    # Enrich with full probability scores from the
    # transformer model (predict_sentiment doesn't
    # expose the raw scores array)
    try:
        from src.models.sentiment import predict as tf_predict
        tf_result = tf_predict(text)
        result["scores"] = tf_result.get("scores", None)
    except Exception:
        pass

    return result


def _run_lime(text: str, model_choice: str,
              model: Any, vectorizer: Any) -> list[dict]:
    """Runs LIME explanation in thread pool."""
    try:
        from src.lime_explainer import explain_prediction
        explanation = explain_prediction(text)
        # explanation is a list of (word, weight) tuples
        if isinstance(explanation, list):
            return [
                {"word": w, "weight": float(wt)}
                for w, wt in explanation
            ]
        elif isinstance(explanation, dict):
            return [
                {"word": k, "weight": float(v)}
                for k, v in explanation.items()
            ]
        return []
    except Exception as e:
        logger.warning(f"LIME failed: {e}")
        return []


def _run_absa(text: str) -> list[dict]:
    """Runs ABSA in thread pool."""
    try:
        from src.models.aspect import analyze_aspects
        aspects = analyze_aspects(text)
        # analyze_aspects returns list of dicts with:
        # aspect, sentiment_label, polarity, subjectivity
        normalized = []
        if isinstance(aspects, list):
            for item in aspects:
                if isinstance(item, dict):
                    # Map sentiment_label to our enum
                    raw_sentiment = item.get(
                        "sentiment_label",
                        item.get("sentiment", "Neutral")
                    )
                    sentiment_val = str(raw_sentiment).lower()
                    if sentiment_val not in [
                        "positive", "negative", "neutral"
                    ]:
                        sentiment_val = "neutral"
                    normalized.append({
                        "aspect": item.get("aspect", ""),
                        "sentiment": sentiment_val,
                        "polarity": float(
                            item.get("polarity", 0.0)),
                        "subjectivity": float(
                            item.get("subjectivity", 0.5)),
                    })
        return normalized
    except Exception as e:
        logger.warning(f"ABSA failed: {e}")
        return []


def _run_sarcasm(text: str) -> dict:
    """Runs sarcasm detection in thread pool."""
    try:
        from src.sarcasm_detector import detect_sarcasm
        result = detect_sarcasm(text)
        # detect_sarcasm returns:
        # is_sarcastic (bool), confidence (float),
        # reason (str), severity (str)
        if isinstance(result, dict):
            return {
                "detected": bool(result.get(
                    "is_sarcastic", False)),
                "confidence": float(result.get(
                    "confidence", 0.0)),
                "reason": result.get("reason", None),
                "irony_score": None,
            }
        elif isinstance(result, bool):
            return {"detected": result,
                    "confidence": 1.0 if result else 0.0}
        return {"detected": False, "confidence": 0.0}
    except Exception as e:
        logger.warning(f"Sarcasm detection failed: {e}")
        return {"detected": False, "confidence": 0.0}


@router.post(
    "",
    response_model=PredictResponse,
    summary="Analyze sentiment of a single review",
    description=(
        "Returns sentiment label, confidence score, "
        "LIME feature importance, aspect-based sentiment "
        "analysis, and sarcasm detection results."
    ),
)
async def predict(
    request: PredictRequest,
    model=Depends(get_model),
    vectorizer=Depends(get_vectorizer),
):
    start_ms = time.perf_counter()
    loop = asyncio.get_event_loop()

    logger.info(
        f"Predict request: model={request.model.value} "
        f"text_len={len(request.text)}"
    )

    # ── Phase 2, Part 1: LRU cache check ──────────────────
    # C9: NEVER cache if include_lime=True — LIME results
    # are user-requested, dynamic, and computationally
    # independent. Skip cache entirely for LIME requests.
    use_cache = not request.include_lime
    cache_key = None

    if use_cache:
        cache_options = {
            "include_absa": request.include_absa,
            "include_sarcasm": request.include_sarcasm,
        }
        cache_key = prediction_cache.get_cache_key(
            request.text, request.model.value, cache_options
        )
        cached = prediction_cache.get(cache_key)
        if cached is not None:
            # CACHE HIT — return immediately
            metrics_store.record_cache_hit()
            elapsed_ms = int(
                (time.perf_counter() - start_ms) * 1000
            )
            logger.info(
                f"Cache HIT: key={cache_key[:8]}... "
                f"[{elapsed_ms}ms]"
            )
            return PredictResponse(
                **cached,
                lime_features=None,
                processing_ms=elapsed_ms,
                cache_hit=True,
            )
        # CACHE MISS — proceed to inference
        metrics_store.record_cache_miss()

    # ── Core prediction (deduplicated + throttled) ────────
    dedup_key = request_deduplicator.make_key(
        request.text, request.model.value
    )

    async def _do_prediction() -> dict:
        async with inference_throttler:
            try:
                return await asyncio.wait_for(
                    loop.run_in_executor(
                        primary_pool.executor,
                        _run_prediction,
                        request.text,
                        request.model.value,
                        model,
                        vectorizer,
                    ),
                    timeout=_INFERENCE_TIMEOUT_S,
                )
            except asyncio.TimeoutError:
                metrics_store.record_timeout()
                logger.error(
                    f"Inference timeout after "
                    f"{_INFERENCE_TIMEOUT_S}s for: "
                    f"{request.text[:50]}"
                )
                raise HTTPException(
                    status_code=504,
                    detail=(
                        "Inference timeout — model took "
                        "too long to respond. "
                        "Please try again."
                    ),
                )

    try:
        result = await request_deduplicator.deduplicate(
            dedup_key, _do_prediction
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Prediction failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Prediction engine error: {str(e)}"
        )

    # ── LIME (optional, NEVER cached — C9) ────────────────
    lime_features = None
    if request.include_lime:
        async with inference_throttler:
            try:
                raw_lime = await asyncio.wait_for(
                    loop.run_in_executor(
                        primary_pool.executor, _run_lime,
                        request.text, request.model.value,
                        model, vectorizer
                    ),
                    timeout=_INFERENCE_TIMEOUT_S,
                )
            except asyncio.TimeoutError:
                metrics_store.record_timeout()
                logger.warning(
                    f"LIME timed out after "
                    f"{_INFERENCE_TIMEOUT_S}s"
                )
                raw_lime = []
        lime_features = [LIMEFeature(**f) for f in raw_lime]

    # ── ABSA (optional, throttled + timeout) ──────────────
    absa_results = None
    if request.include_absa:
        async with inference_throttler:
            try:
                raw_absa = await asyncio.wait_for(
                    loop.run_in_executor(
                        primary_pool.executor, _run_absa,
                        request.text
                    ),
                    timeout=_INFERENCE_TIMEOUT_S,
                )
            except asyncio.TimeoutError:
                metrics_store.record_timeout()
                logger.warning(
                    f"ABSA timed out after "
                    f"{_INFERENCE_TIMEOUT_S}s"
                )
                raw_absa = []
        absa_results = []
        for item in raw_absa:
            sentiment_val = item.get("sentiment", "neutral")
            if sentiment_val not in ["positive", "negative",
                                      "neutral"]:
                sentiment_val = "neutral"
            absa_results.append(ABSAItem(
                aspect=item["aspect"],
                sentiment=SentimentLabel(sentiment_val),
                polarity=item["polarity"],
                subjectivity=item["subjectivity"],
            ))

    # ── Sarcasm (optional, throttled + timeout) ───────────
    sarcasm_result = None
    if request.include_sarcasm:
        async with inference_throttler:
            try:
                raw_sarcasm = await asyncio.wait_for(
                    loop.run_in_executor(
                        primary_pool.executor, _run_sarcasm,
                        request.text
                    ),
                    timeout=_INFERENCE_TIMEOUT_S,
                )
            except asyncio.TimeoutError:
                metrics_store.record_timeout()
                logger.warning(
                    f"Sarcasm timed out after "
                    f"{_INFERENCE_TIMEOUT_S}s"
                )
                raw_sarcasm = {
                    "detected": False,
                    "confidence": 0.0,
                }
        sarcasm_result = SarcasmResult(**raw_sarcasm)

    # ── Normalize core result ──────────────────────────────
    label_name = result.get("label_name", "Neutral")
    sentiment_raw = label_name.lower()
    if sentiment_raw not in ["positive", "negative", "neutral"]:
        sentiment_raw = "neutral"

    # O5: Centralized confidence normalization (0-1 → 0-100)
    raw_confidence = float(result.get("confidence", 0.0))
    confidence_pct = normalize_confidence(raw_confidence)

    # B1: Shared sentiment corrections (double negatives,
    # mixed "but" clauses) — applied in both /predict and
    # /language routes for consistency.
    from app.sentiment_corrections import (
        apply_sentiment_corrections,
    )
    sentiment_raw, confidence_pct, _was_corrected = (
        apply_sentiment_corrections(
            request.text, sentiment_raw, confidence_pct
        )
    )

    # Build probabilities from scores if available
    scores = result.get("scores", None)
    if scores and len(scores) == 3:
        probas = {
            "negative": float(scores[0]),
            "neutral": float(scores[1]),
            "positive": float(scores[2]),
        }
    else:
        probas = {sentiment_raw: raw_confidence}

    elapsed_ms = int(
        (time.perf_counter() - start_ms) * 1000
    )
    logger.info(
        f"Predict complete: {sentiment_raw} "
        f"conf={confidence_pct:.1f}% "
        f"[{elapsed_ms}ms]"
        f"{' [corrected]' if _was_corrected else ''}"
    )

    response = PredictResponse(
        sentiment=SentimentLabel(sentiment_raw),
        confidence=confidence_pct,
        polarity=float(result.get("polarity", 0.0)),
        subjectivity=float(result.get("subjectivity", 0.0)),
        probabilities={k: float(v)
                       for k, v in probas.items()},
        lime_features=lime_features,
        absa=absa_results,
        sarcasm=sarcasm_result,
        model_used=result.get("model_used",
                              request.model.value),
        processing_ms=elapsed_ms,
        cache_hit=False,
    )

    # ── Phase 2, Part 1: Cache store ──────────────────────
    # Store successful prediction in cache (strip LIME,
    # processing_ms, and cache_hit — transient fields).
    # C9 enforced: use_cache=False when include_lime=True.
    if use_cache and cache_key:
        cache_data = response.model_dump()
        cache_data.pop("lime_features", None)
        cache_data.pop("processing_ms", None)
        cache_data.pop("cache_hit", None)
        prediction_cache.set(cache_key, cache_data)

    # Record prediction for live dashboard stats
    metrics_store.record_prediction(sentiment_raw, "English")

    return response
