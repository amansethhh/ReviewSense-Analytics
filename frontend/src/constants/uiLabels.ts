/**
 * ReviewSense — Centralized UI labels.
 * 
 * All display-facing label strings live here so that
 * future pages automatically inherit any wording change.
 */

export const UI_LABELS = {
  /* ── Model Selection ─────────────────────── */
  MODEL_DISPLAY_NOTE: 'Display only — predictions use Hybrid Transformer Pipeline.',

  /* ── User Rating ─────────────────────────── */
  USER_RATING: 'User Rating (Optional)',
  USER_RATING_HELP: 'Helps validate sentiment (does not affect prediction)',

  /* ── Content Type (Domain) ───────────────── */
  CONTENT_TYPE: 'Content Type (Optional)',
  CONTENT_TYPE_HELP: 'Used for contextual analysis (does not affect sentiment prediction)',
} as const
