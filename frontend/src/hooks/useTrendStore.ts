/**
 * useTrendStore — global persistent trend store backed by localStorage.
 *
 * Stores one TrendPoint per completed batch job (Bulk or Language Batch).
 * The ModelDashboard reads all points and re-renders whenever a new batch
 * completes anywhere in the app (via the `storage` event).
 *
 * FIX: Uses a monotonic counter stored alongside the points to guarantee
 * unique Job labels even after the array is trimmed to MAX_POINTS.
 */
import { useState, useEffect, useCallback } from 'react'

export interface TrendPoint {
  /** Label shown on X-axis, e.g. "Job 1", "Job 2" */
  month: string          // kept as "month" for backward-compat with SentimentTrendChart
  positive: number       // % rounded integer
  negative: number
  neutral: number
  /** ISO timestamp for this batch completion */
  ts: string
  /** Total rows processed in this job */
  total: number
  /** Unique job counter (monotonic, never resets) */
  jobIndex: number
}

const LS_KEY = 'rs_sentiment_trend_v2'
const LS_COUNTER_KEY = 'rs_sentiment_trend_counter'
const MAX_POINTS = 20   // keep last 20 jobs max

/** Read all stored points from localStorage */
function readPoints(): TrendPoint[] {
  try {
    const raw = localStorage.getItem(LS_KEY)
    if (!raw) {
      // Migrate from v1 if it exists
      const v1 = localStorage.getItem('rs_sentiment_trend_v1')
      if (v1) {
        try {
          const v1Points = JSON.parse(v1) as TrendPoint[]
          // Re-index with monotonic counter
          const migrated = v1Points.map((p, i) => ({
            ...p,
            jobIndex: i + 1,
            month: `Job ${i + 1}`,
          }))
          localStorage.setItem(LS_KEY, JSON.stringify(migrated))
          localStorage.setItem(LS_COUNTER_KEY, String(migrated.length))
          localStorage.removeItem('rs_sentiment_trend_v1')
          return migrated
        } catch {
          return []
        }
      }
      return []
    }
    return JSON.parse(raw) as TrendPoint[]
  } catch {
    return []
  }
}

/** Get the next monotonic counter value */
function getNextCounter(): number {
  try {
    const raw = localStorage.getItem(LS_COUNTER_KEY)
    const current = raw ? parseInt(raw, 10) : 0
    return isNaN(current) ? 1 : current + 1
  } catch {
    return 1
  }
}

/** Append a new point (capped at MAX_POINTS) and fire a storage-like event.
 *  Uses a separate monotonic counter so "Job N" labels are always unique
 *  even after the array is trimmed. */
function writePoint(point: Omit<TrendPoint, 'month' | 'ts' | 'jobIndex'>): TrendPoint[] {
  const existing = readPoints()

  // Monotonic counter — stored independently so it never resets on trim
  const nextIdx = getNextCounter()

  const now = new Date()
  const timeLabel = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`

  const newPoint: TrendPoint = {
    month: `Job ${nextIdx} (${timeLabel})`,
    ts: now.toISOString(),
    jobIndex: nextIdx,
    ...point,
  }

  // Only deduplicate if exact same job within 5 seconds (accidental double-push)
  const last = existing[existing.length - 1]
  if (last
    && last.positive === newPoint.positive
    && last.negative === newPoint.negative
    && last.neutral === newPoint.neutral
    && last.total === newPoint.total
    && (new Date(newPoint.ts).getTime() - new Date(last.ts).getTime()) < 5000
  ) {
    return existing
  }

  const updated = [...existing, newPoint].slice(-MAX_POINTS)

  // Persist both the points and the counter
  localStorage.setItem(LS_KEY, JSON.stringify(updated))
  localStorage.setItem(LS_COUNTER_KEY, String(nextIdx))

  // Fire a custom event so other tabs / components react
  window.dispatchEvent(new StorageEvent('storage', {
    key: LS_KEY,
    newValue: JSON.stringify(updated),
  }))
  return updated
}

/** Add a completed batch result to the global trend store.
 *  Pass the raw results array from useBulk or LanguageAnalysisPage.
 *  Deduplication: ignores pushes with identical results within 5s. */
export function pushTrendPoint(
  results: Array<{ sentiment: string }>,
) {
  if (!results || results.length < 1) return
  const total = results.length
  const positive = Math.round(results.filter(r => r.sentiment === 'positive').length / total * 100)
  const negative = Math.round(results.filter(r => r.sentiment === 'negative').length / total * 100)
  const neutral  = Math.round(results.filter(r => r.sentiment === 'neutral').length  / total * 100)
  writePoint({ positive, negative, neutral, total })
}

/** React hook — subscribes to the trend store and returns live points.
 *  Re-renders whenever pushTrendPoint() is called anywhere. */
export function useTrendStore(): TrendPoint[] {
  const [points, setPoints] = useState<TrendPoint[]>(readPoints)

  useEffect(() => {
    function onStorage(e: StorageEvent) {
      if (e.key === LS_KEY) {
        setPoints(readPoints())
      }
    }
    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [])

  const refresh = useCallback(() => setPoints(readPoints()), [])

  // Also poll every 3 s so same-tab updates are caught
  useEffect(() => {
    const id = setInterval(refresh, 3000)
    return () => clearInterval(id)
  }, [refresh])

  return points
}
