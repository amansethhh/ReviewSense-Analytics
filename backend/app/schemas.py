from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal, Any
from enum import Enum

# ── Enums ──────────────────────────────────────────────────


class SentimentLabel(str, Enum):
    positive  = "positive"
    negative  = "negative"
    neutral   = "neutral"
    # V3: "uncertain" REMOVED — only 3 labels allowed
    # "unknown" and "error" kept for edge cases (timeouts, failures)
    unknown   = "unknown"
    error     = "error"


class ModelChoice(str, Enum):
    best       = "best"
    linearsvc  = "LinearSVC"
    logreg     = "LogisticRegression"
    naivebayes = "NaiveBayes"
    rf         = "RandomForest"


class DomainChoice(str, Enum):
    all     = "all"
    food    = "food"
    ecom    = "ecom"
    movie   = "movie"
    product = "product"


# ── /predict ───────────────────────────────────────────────

class PredictRequest(BaseModel):
    text: str = Field(
        ...,
        min_length=1,
        max_length=10000,
        description="Review text to analyze"
    )
    model: ModelChoice = ModelChoice.best
    domain: DomainChoice = DomainChoice.all
    star_rating: Optional[int] = Field(
        None, ge=1, le=5,
        description="Optional user-provided star rating"
    )
    include_lime: bool = True
    include_absa: bool = True
    include_sarcasm: bool = True

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError(
                "text must not be empty or whitespace only"
            )
        return v.strip()


class LIMEFeature(BaseModel):
    word:   str
    weight: float


class ABSAItem(BaseModel):
    aspect:      str
    sentiment:   SentimentLabel
    polarity:    float
    subjectivity: float


class SarcasmResult(BaseModel):
    detected:    bool
    confidence:  float
    reason:      Optional[str] = None
    irony_score: Optional[float] = None


class PredictResponse(BaseModel):
    label:       Optional[SentimentLabel] = None
    sentiment:   SentimentLabel
    raw_label:   str = "neutral"
    is_uncertain: bool = False
    confidence:  float = Field(..., ge=0.0, le=100.0)
    polarity:    float = Field(..., ge=-1.0, le=1.0)
    subjectivity: float = Field(..., ge=0.0, le=1.0)
    probabilities: dict[str, float]
    lime_features: Optional[list[LIMEFeature]] = None
    absa:          Optional[list[ABSAItem]]    = None
    sarcasm:       Optional[SarcasmResult]     = None
    model_used:    str
    processing_ms: int
    cache_hit:     bool = False
    # V3 output contract fields
    language:              Optional[str] = "en"
    language_code:         Optional[str] = "en"
    analysis_input_source: str = "original"
    translation:           Optional[str] = None
    translation_failed:    bool = False
    neutral_corrected:     bool = False
    sarcasm_applied:       bool = False


# ── /bulk ──────────────────────────────────────────────────

class BulkJobStatus(str, Enum):
    queued     = "queued"
    processing = "processing"
    completed  = "completed"
    failed     = "failed"


class BulkJobSubmitResponse(BaseModel):
    job_id:        str
    status:        BulkJobStatus
    total_rows:    int
    estimated_seconds: int
    poll_url:      str


class BulkRowResult(BaseModel):
    row_index:   int
    text:        str
    label:       Optional[SentimentLabel] = None
    sentiment:   SentimentLabel
    raw_label:   str = "neutral"
    is_uncertain: bool = False
    confidence:  float
    polarity:    float
    subjectivity: float
    sarcasm_detected: Optional[bool] = None
    aspects:     Optional[list[ABSAItem]] = None
    detected_language: Optional[str] = None
    translation_method: Optional[str] = None
    translated_text: Optional[str] = None
    translation: Optional[str] = None
    # V3 output contract fields
    analysis_input_source: str = "original"
    translation_failed:    bool = False
    neutral_corrected:     bool = False


class BulkJobResult(BaseModel):
    job_id:       str
    status:       BulkJobStatus
    progress:     float = Field(..., ge=0.0, le=100.0)
    total_rows:   int
    processed:    int
    results:      Optional[list[BulkRowResult]] = None
    summary:      Optional[dict[str, Any]] = None
    error:        Optional[str] = None
    logs:         list[str] = Field(default_factory=list)
    phase:        Optional[str] = None
    # Live cumulative sentiment counts (accurate totals, not 50-row window)
    live_pos:     Optional[int] = None
    live_neg:     Optional[int] = None
    live_neu:     Optional[int] = None
    live_sarcasm: Optional[int] = None


# ── /language ──────────────────────────────────────────────

class LanguageRequest(BaseModel):
    text: str = Field(
        ..., min_length=1, max_length=10000
    )
    model: ModelChoice = ModelChoice.best
    domain: DomainChoice = DomainChoice.all
    star_rating: Optional[int] = Field(
        None, ge=1, le=5,
        description="Optional user-provided star rating"
    )
    include_lime: bool = True
    include_absa: bool = True
    include_sarcasm: bool = True

    @field_validator("text")
    @classmethod
    def text_must_not_be_blank(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("text must not be blank")
        return v.strip()


class LanguageResponse(BaseModel):
    detected_language:      str
    language_code:          str
    detection_confidence:   float
    translated_text:        Optional[str] = None
    translation:            Optional[str] = None
    translation_needed:     bool
    skipped_translation:    bool = False
    label:                  Optional[SentimentLabel] = None
    sentiment:              SentimentLabel
    raw_label:              str = "neutral"
    is_uncertain:           bool = False
    confidence:             float
    polarity:               float
    subjectivity:           float
    model_used:             str
    processing_ms:          int
    lime_features:          Optional[list[LIMEFeature]] = None
    absa:                   Optional[list[ABSAItem]] = None
    sarcasm:                Optional[SarcasmResult] = None
    # V3 output contract fields
    analysis_input_source:  str = "original"
    translation_failed:     bool = False
    neutral_corrected:      bool = False
    sarcasm_applied:        bool = False


# ── /metrics ───────────────────────────────────────────────

class ModelMetric(BaseModel):
    name:         str
    accuracy:     float
    macro_f1:     float
    weighted_f1:  float
    macro_prec:   float
    train_time_s: float
    auc:          float
    is_best:      bool
    description:  Optional[str] = None


class ConfusionMatrixData(BaseModel):
    model_name: str
    labels:     list[str]
    matrix:     list[list[int]]


class MetricsResponse(BaseModel):
    models:            list[ModelMetric]
    best_model:        str
    dataset_size:      int
    feature_count:     int
    class_distribution: dict[str, int]
    confusion_matrices: list[ConfusionMatrixData]
    generated_at:      str
    model_version_hash: str = ""
    runtime_metrics:   dict = {}


# ── Error ──────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    error:   str
    detail:  Optional[str] = None
    code:    int


# ── /feedback ─────────────────────────────────────────────

class FeedbackRequest(BaseModel):
    text: str
    predicted_sentiment: SentimentLabel
    correct_sentiment: SentimentLabel
    confidence: float
    source: str = "live_prediction"
    notes: Optional[str] = None


class FeedbackResponse(BaseModel):
    feedback_id: str
    message: str
    total_feedback_collected: int
