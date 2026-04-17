/**
 * useTrendStore — global persistent trend store backed by localStorage.
 *
 * Stores one TrendPoint per completed batch job (Bulk or Language Batch).
 * The ModelDashboard reads all points and re-renders whenever a new batch
 * completes anywhere in the app (via the `storage` event).
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
}

const LS_KEY = 'rs_sentiment_trend_v1'
const MAX_POINTS = 20   // keep last 20 jobs max

/** Read all stored points from localStorage */
function readPoints(): TrendPoint[] {
  try {
    const raw = localStorage.getItem(LS_KEY)
    if (!raw) return []
    return JSON.parse(raw) as TrendPoint[]
  } catch {
    return []
  }
}

/** Append a new point (capped at MAX_POINTS) and fire a storage-like event */
function writePoint(point: Omit<TrendPoint, 'month' | 'ts'>): TrendPoint[] {
  const existing = readPoints()
  const idx = existing.length + 1
  const newPoint: TrendPoint = {
    month: `Job ${idx}`,
    ts: new Date().toISOString(),
    ...point,
  }
  const updated = [...existing, newPoint].slice(-MAX_POINTS)
  localStorage.setItem(LS_KEY, JSON.stringify(updated))
  // Fire a custom event so other tabs / components react
  window.dispatchEvent(new StorageEvent('storage', {
    key: LS_KEY,
    newValue: JSON.stringify(updated),
  }))
  return updated
}

/** Add a completed batch result to the global trend store.
 *  Pass the raw results array from useBulk or LanguageAnalysisPage. */
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
