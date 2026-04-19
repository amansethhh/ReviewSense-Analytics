"""
W4-2: User feedback collection endpoint.
Stores feedback in-memory + persists to data/feedback.jsonl.
"""
import uuid
import json
import logging
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter

from app.schemas import (
    FeedbackRequest, FeedbackResponse,
)

router = APIRouter()
logger = logging.getLogger("reviewsense.feedback")

# In-memory store + JSONL persistence
_feedback_store: list[dict] = []
_FEEDBACK_FILE = Path("data/feedback.jsonl")


@router.post(
    "/submit",
    response_model=FeedbackResponse,
    summary="Submit user feedback on a prediction",
)
async def submit_feedback(request: FeedbackRequest):
    """Record user feedback for a sentiment prediction."""
    entry = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now().isoformat(),
        "text": request.text,
        "predicted": request.predicted_sentiment.value,
        "correct": request.correct_sentiment.value,
        "confidence": request.confidence,
        "source": request.source,
        "notes": request.notes,
        "is_correction": (
            request.predicted_sentiment
            != request.correct_sentiment
        ),
    }
    _feedback_store.append(entry)

    # Persist to JSONL file
    try:
        _FEEDBACK_FILE.parent.mkdir(
            parents=True, exist_ok=True)
        with open(_FEEDBACK_FILE, "a",
                  encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        logger.warning(f"Failed to persist feedback: {e}")

    return FeedbackResponse(
        feedback_id=entry["id"],
        message="Thank you for your feedback!",
        total_feedback_collected=len(_feedback_store),
    )


@router.get(
    "/stats",
    summary="Get feedback statistics",
)
async def get_feedback_stats():
    """Return summary statistics of collected feedback."""
    total = len(_feedback_store)
    corrections = sum(
        1 for f in _feedback_store if f["is_correction"]
    )
    by_source: dict[str, int] = {}
    for f in _feedback_store:
        src = f.get("source", "unknown")
        by_source[src] = by_source.get(src, 0) + 1

    return {
        "total_feedback": total,
        "corrections": corrections,
        "correction_rate_pct": (
            round(corrections / total * 100, 2)
            if total else 0.0
        ),
        "by_source": by_source,
    }
