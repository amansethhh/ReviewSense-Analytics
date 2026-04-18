import { useState, useEffect, useRef, useCallback } from 'react'
import { getLiveStats } from '@/api/api'
import type { LiveStatsResponse } from '@/types/api.types'

const POLL_INTERVAL_MS = 3000

/** Default "zero" live stats — renders the 4 corner panels instantly
 *  with zeroed-out values while the first real fetch completes. */
const LIVE_DEFAULTS: LiveStatsResponse = {
  total_predictions: 0,
  total_requests: 0,
  avg_latency_ms: 0,
  cache_hit_rate: 0,
  uptime_seconds: 0,
  errors: 0,
  inference_timeouts: 0,
  sentiment_distribution: {},
  sentiment_total: 0,
  language_distribution: {},
  active_model: '—',
  models_loaded: 0,
  pipeline_config: {
    sarcasm: false,
    absa: false,
    multilingual: false,
    cache_enabled: false,
  },
}

/**
 * Polls /metrics/live every 3 seconds for real-time
 * dashboard panel data. Stops polling on unmount.
 *
 * @param initialData - Optional cached snapshot from the store.
 *        If provided, the hook starts with this data (no null → data flash).
 *        If not provided, falls back to LIVE_DEFAULTS (zeroed-out values).
 */
export function useLiveStats(initialData?: LiveStatsResponse | null) {
  const [data, setData] = useState<LiveStatsResponse>(initialData || LIVE_DEFAULTS)
  const [loading, setLoading] = useState(!initialData)
  const [error, setError] = useState<string | null>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const activeRef = useRef(true)

  const poll = useCallback(async () => {
    if (!activeRef.current) return
    try {
      const stats = await getLiveStats()
      if (activeRef.current) {
        setData(stats)
        setError(null)
        setLoading(false)
      }
    } catch (err) {
      if (activeRef.current) {
        setError(err instanceof Error ? err.message : 'Failed to load live stats')
        setLoading(false)
      }
    }
    if (activeRef.current) {
      timerRef.current = setTimeout(poll, POLL_INTERVAL_MS)
    }
  }, [])

  useEffect(() => {
    activeRef.current = true
    poll()
    return () => {
      activeRef.current = false
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [poll])

  return { data, loading, error }
}
