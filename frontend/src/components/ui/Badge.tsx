import React from 'react';
import type { SentimentLabel } from '@/types/api.types';

/* ── Generic Badge (unchanged) ── */

interface BadgeProps {
  label:    string;
  variant?: 'positive' | 'negative' | 'neutral' | 'uncertain' | 'unknown'
          | 'primary' | 'default';
}

export function Badge({ label, variant = 'default' }: BadgeProps) {
  return (
    <span className={`badge badge--${variant}`}>
      {label}
    </span>
  );
}


/* ══════════════════════════════════════════════════════════
   Three-Tier SentimentBadge — G1 Fix
   ══════════════════════════════════════════════════════════

   TIER 1: ERROR      — confidence === 0 OR sentiment === 'unknown'
   TIER 2: LOW CONF   — 0 < confidence < 50
   TIER 3: NORMAL     — confidence >= 50
   ══════════════════════════════════════════════════════════ */

interface SentimentBadgeProps {
  sentiment:          SentimentLabel;
  confidence?:        number;           // 0–100
  translationMethod?: string | null;    // 'helsinki' | 'google' | 'failed'
  showConfidence?:    boolean;
  size?:              'sm' | 'md' | 'lg';
}

function getSentimentColor(s: string): { bg: string; text: string; border: string } {
  switch (s.toLowerCase()) {
    case 'positive':
      return { bg: 'rgba(34,197,94,0.12)', text: 'var(--color-positive,#22c55e)', border: 'rgba(34,197,94,0.30)' };
    case 'negative':
      return { bg: 'rgba(244,63,94,0.12)', text: 'var(--color-negative,#f43f5e)', border: 'rgba(244,63,94,0.30)' };
    case 'neutral':
      return { bg: 'rgba(245,158,11,0.12)', text: 'var(--color-neutral-sent,#f59e0b)', border: 'rgba(245,158,11,0.30)' };
    case 'uncertain':
      return { bg: 'rgba(251,146,60,0.12)', text: '#fb923c', border: 'rgba(251,146,60,0.30)' };
    case 'unknown':
      return { bg: 'rgba(122,121,116,0.12)', text: 'var(--color-text-muted,#7a7974)', border: 'rgba(122,121,116,0.30)' };
    case 'error':
      return { bg: 'rgba(161,44,123,0.12)', text: 'var(--color-error,#f43f5e)', border: 'rgba(161,44,123,0.30)' };
    default:
      return { bg: 'rgba(122,121,116,0.12)', text: '#7a7974', border: 'rgba(122,121,116,0.3)' };
  }
}

function sentimentDisplayLabel(s: string): string {
  switch (s.toLowerCase()) {
    case 'positive':  return 'Positive';
    case 'negative':  return 'Negative';
    case 'neutral':   return 'Neutral';
    case 'uncertain': return '\u26a0 Uncertain';
    case 'unknown':   return '\u26a0 Timeout';
    case 'error':     return '\u2715 Error';
    default:          return s;
  }
}

export function SentimentBadge({
  sentiment,
  confidence,
  translationMethod,
  showConfidence = true,
  size = 'sm',
}: SentimentBadgeProps) {
  const conf = confidence ?? 0;
  // 'unknown' = translation timeout → grey badge (not ERROR)
  // 'error'   = hard exception     → red badge
  const isTimeout = sentiment === 'unknown';
  const isError = sentiment === 'error'
    || (conf === 0.0 && !isTimeout && translationMethod === 'failed');
  const isLowConf = !isError && !isTimeout && conf > 0.0 && conf < 50.0;

  const sizeStyles: Record<string, React.CSSProperties> = {
    sm: { fontSize: '12px', padding: '3px 10px' },
    md: { fontSize: '14px', padding: '5px 14px' },
    lg: { fontSize: 'var(--text-lg)', padding: '0.5rem 1.5rem' },
  };

  /* ── TIER 1-A: TIMEOUT (grey) ── */
  if (isTimeout) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', justifyContent: 'center' }}>
        <span
          style={{
            display: 'inline-flex', alignItems: 'center', gap: '4px',
            ...sizeStyles[size],
            borderRadius: '9999px', fontWeight: 600,
            backgroundColor: 'rgba(122,121,116,0.15)',
            color: 'var(--color-text-muted,#7a7974)',
            border: '1px solid rgba(122,121,116,0.35)',
            cursor: 'help',
          }}
          title="Translation timed out for this language. Sentiment analysis was skipped — result is unreliable."
        >
          <span style={{ fontSize: '11px' }}>⚠</span>
          Timeout
        </span>
      </div>
    );
  }

  /* ── TIER 1-B: ERROR (red) ── */
  if (isError) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', justifyContent: 'center' }}>
        <span
          style={{
            display: 'inline-flex', alignItems: 'center', gap: '4px',
            ...sizeStyles[size],
            borderRadius: '9999px', fontWeight: 600,
            backgroundColor: 'rgba(244,63,94,0.15)',
            color: '#f43f5e',
            border: '1px solid rgba(244,63,94,0.35)',
            cursor: 'help',
          }}
          title="Analysis failed: The model returned zero confidence. This result is unreliable."
        >
          <span style={{ fontSize: '11px' }}>⚠</span>
          ERROR
        </span>
        {translationMethod === 'failed' && (
          <span
            style={{ fontSize: '11px', color: '#f43f5e', cursor: 'help' }}
            title="Translation failed — original text was used for analysis. Accuracy may be very low."
          >
            Translation failed
          </span>
        )}
      </div>
    );
  }

  /* ── TIER 2: LOW CONFIDENCE ── */
  if (isLowConf) {
    const clr = getSentimentColor(sentiment);
    return (
      <div style={{ display: 'flex', alignItems: 'center', gap: '6px', justifyContent: 'center' }}>
        <span
          style={{
            display: 'inline-flex', alignItems: 'center', gap: '4px',
            ...sizeStyles[size],
            borderRadius: '9999px', fontWeight: 600,
            backgroundColor: clr.bg, color: clr.text,
            border: `1px solid ${clr.border}`,
            opacity: 0.75,
          }}
        >
          {sentimentDisplayLabel(sentiment)}
        </span>
        {showConfidence && (
          <span
            style={{
              fontSize: '12px', color: '#d19900', fontWeight: 500,
              cursor: 'help',
            }}
            title={`Low confidence (${conf.toFixed(1)}%) — result may be inaccurate`}
          >
            ⚠ {conf.toFixed(1)}%
          </span>
        )}
      </div>
    );
  }

  /* ── TIER 3: NORMAL ── */
  const clr = getSentimentColor(sentiment);
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: '6px', justifyContent: 'center' }}>
      <span
        style={{
          display: 'inline-flex', alignItems: 'center',
          ...sizeStyles[size],
          borderRadius: '9999px', fontWeight: 600,
          backgroundColor: clr.bg, color: clr.text,
          border: `1px solid ${clr.border}`,
        }}
      >
        {sentimentDisplayLabel(sentiment)}
      </span>
      {showConfidence && (
        <span style={{ fontSize: '13px', color: 'var(--color-text-muted,#7a7974)', fontWeight: 500 }}>
          {conf.toFixed(1)}%
        </span>
      )}
    </div>
  );
}

/* ── Error/Warning Summary Banner ── */

interface ErrorSummaryProps {
  results: Array<{ confidence: number; sentiment: string }>;
}

export function AnalysisErrorSummary({ results }: ErrorSummaryProps) {
  const errorCount = results.filter(r => r.confidence === 0.0 || r.sentiment === 'unknown').length;
  const lowConfCount = results.filter(r => r.confidence > 0.0 && r.confidence < 50.0).length;

  if (errorCount === 0 && lowConfCount === 0) return null;

  return (
    <div style={{
      padding: '10px 16px',
      backgroundColor: errorCount > 0 ? 'rgba(244,63,94,0.08)' : 'rgba(209,153,0,0.08)',
      border: `1px solid ${errorCount > 0 ? 'rgba(244,63,94,0.2)' : 'rgba(209,153,0,0.2)'}`,
      borderRadius: '8px',
      marginTop: '12px',
      fontSize: '13px',
      color: errorCount > 0 ? '#f43f5e' : '#d19900',
      display: 'flex',
      alignItems: 'center',
      gap: '8px',
    }}>
      <span style={{ fontSize: '15px' }}>⚠</span>
      <span>
        {errorCount > 0 && (
          <>{errorCount} review{errorCount !== 1 ? 's' : ''} could not be analyzed (shown as ERROR). </>
        )}
        {lowConfCount > 0 && (
          <>{lowConfCount} review{lowConfCount !== 1 ? 's have' : ' has'} low confidence (&lt;50%).</>
        )}
      </span>
    </div>
  );
}

export default SentimentBadge;
