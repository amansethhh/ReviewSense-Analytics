# Week 4 — Production Hardening Backlog
## Status: DEFERRED — Target: May 1, 2026

### W4-1: Translation Error Rate Tracking
**What:** Log every translation failure to a local JSON file (not Sentry — no external service needed)
**File:** backend/app/routes/language.py — add `_log_translation_error(text, language, error)` function
**Format:** `logs/translation_errors.jsonl` — one JSON object per line
**Why:** Understand how often Helsinki-NLP fails and which language pairs are worst
**Effort:** ~2 hours

### W4-2: User Feedback Button on Results
**What:** Small "Was this correct?" thumbs up/down button on each result row
**File:** frontend/src/components/ui/Badge.tsx (extend) + new POST /feedback endpoint
**Storage:** feedback.jsonl in project root (no database needed)
**Why:** Ground truth data to improve accuracy over time
**Effort:** ~4 hours

### W4-3: Admin Translation Quality Dashboard
**What:** A hidden /admin page that reads translation_errors.jsonl and feedback.jsonl
**Shows:** Error rate by language, top failing inputs, confidence distribution histogram
**File:** frontend/src/pages/AdminPage.tsx (new) + backend GET /admin/stats endpoint
**Why:** Visibility into system health without external monitoring
**Effort:** ~6 hours

### W4-4: Retry Logic for deep-translator Network Failures
**What:** If deep-translator (Google) fails due to network timeout, retry up to 2 times with 500ms backoff
**File:** backend/app/routes/language.py — _translate_with_fallback()
**Why:** Prevents a transient network blip from making an entire multilingual bulk job fail
**Effort:** ~1 hour

### Implementation Order
W4-4 → W4-1 → W4-2 → W4-3
