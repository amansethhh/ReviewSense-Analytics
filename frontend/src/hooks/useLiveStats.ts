import { useState, useEffect, useRef, useCallback } from 'react'
import { getLiveStats } from '@/api/api'
import type { LiveStatsResponse } from '@/types/api.types'

const POLL_INTERVAL_MS = 3000

/**
 * Polls /metrics/live every 3 seconds for real-time
 * dashboard panel data. Stops polling on unmount.
 */
export function useLiveStats() {
  const [data, setData] = useState<LiveStatsResponse | null>(null)
  const [loading, setLoading] = useState(true)
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
