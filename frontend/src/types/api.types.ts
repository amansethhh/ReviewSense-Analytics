// These mirror the Pydantic schemas in backend/app/schemas.py
// exactly. Keep in sync if schemas.py changes.

export type SentimentLabel = 'positive' | 'negative' | 'neutral' | 'unknown' | 'error'
export type ModelChoice =
  | 'best' | 'LinearSVC' | 'LogisticRegression'
  | 'NaiveBayes' | 'RandomForest'
export type DomainChoice =
  | 'all' | 'food' | 'ecom' | 'movie' | 'product'
export type BulkJobStatus =
  | 'queued' | 'processing' | 'completed' | 'failed'

// ── /predict ────────────────────────────────────────

export interface PredictRequest {
  text:              string
  model?:            ModelChoice
  domain?:           DomainChoice
  star_rating?:      number | null
  include_lime?:     boolean
  include_absa?:     boolean
  include_sarcasm?:  boolean
}

export interface LIMEFeature {
  word:   string
  weight: number
}

export interface ABSAItem {
  aspect:       string
  sentiment:    SentimentLabel
  polarity:     number
  subjectivity: number
}

export interface SarcasmResult {
  detected:    boolean
  confidence:  number
  reason?:     string | null
  irony_score?: number | null
}

export interface PredictResponse {
  sentiment:     SentimentLabel
  confidence:    number        // 0–100
  polarity:      number        // -1 to 1
  subjectivity:  number        // 0–1
  probabilities: Record<string, number>
  lime_features?: LIMEFeature[] | null
  absa?:          ABSAItem[]   | null
  sarcasm?:       SarcasmResult | null
  model_used:    string
  processing_ms: number
}

// ── /bulk ───────────────────────────────────────────

export interface BulkJobSubmitResponse {
  job_id:             string
  status:             BulkJobStatus
  total_rows:         number
  estimated_seconds:  number
  poll_url:           string
}

export interface BulkRowResult {
  row_index:            number
  text:                 string
  sentiment:            SentimentLabel
  confidence:           number
  polarity:             number
  subjectivity:         number
  sarcasm_detected?:    boolean | null
  aspects?:             ABSAItem[] | null
  detected_language?:   string | null
  translation_method?:  string | null
  translated_text?:     string | null
}

export interface BulkJobResult {
  job_id:     string
  status:     BulkJobStatus
  progress:   number
  total_rows: number
  processed:  number
  results?:   BulkRowResult[] | null
  summary?:   BulkSummary    | null
  error?:     string | null
  logs:       string[]
}

export interface BulkSummary {
  total_analyzed: number
  positive:       number
  negative:       number
  neutral:        number
  positive_pct:   number
  negative_pct:   number
  neutral_pct:    number
  sarcasm_count:  number
}

// ── /language ───────────────────────────────────────

export interface LanguageRequest {
  text:   string
  model?: ModelChoice
}

export interface LanguageResponse {
  detected_language:    string
  language_code:        string
  detection_confidence: number
  translated_text?:     string | null
  translation_needed:   boolean
  sentiment:            SentimentLabel
  confidence:           number
  polarity:             number
  subjectivity:         number
  model_used:           string
  processing_ms:        number
}

// ── /metrics ────────────────────────────────────────

export interface ModelMetric {
  name:         string
  accuracy:     number
  macro_f1:     number
  weighted_f1:  number
  macro_prec:   number
  train_time_s: number
  auc:          number
  is_best:      boolean
  description?: string | null
}

export interface ConfusionMatrixData {
  model_name: string
  labels:     string[]
  matrix:     number[][]
}

export interface MetricsResponse {
  models:             ModelMetric[]
  best_model:         string
  dataset_size:       number
  feature_count:      number
  class_distribution: Record<string, number>
  confusion_matrices: ConfusionMatrixData[]
  generated_at:       string
}

// ── API Error ────────────────────────────────────────

export interface ApiError {
  error:   string
  detail?: string | null
  code:    number
}

// ── /metrics/translations ─────────────────────────────

export interface TranslationMetrics {
  total_translations: number
  method_breakdown: {
    helsinki_success: number
    google_success:  number
    failed:          number
    skipped_english: number
  }
  failure_rate_pct: number
  per_language: Record<string, { count: number; failed: number }>
}

// ── /feedback ───────────────────────────────────────

export interface FeedbackRequest {
  text:                string
  predicted_sentiment: SentimentLabel
  correct_sentiment:   SentimentLabel
  confidence:          number
  source:              string
  notes?:              string | null
}

export interface FeedbackResponse {
  feedback_id:              string
  message:                  string
  total_feedback_collected:  number
}
