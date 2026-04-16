import { useState, useEffect } from 'react'
import { getMetrics } from '@/api/api'
import { useApp } from '@/context/AppContext'

export function useMetrics() {
  const { state, dispatch, showToast } = useApp()
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState<string | null>(null)

  useEffect(() => {
    // Use cache if available
    if (state.metricsCache) return

    setLoading(true)
    getMetrics()
      .then(data => {
        dispatch({ type: 'SET_METRICS', payload: data })
      })
      .catch(err => {
        const msg = err instanceof Error
          ? err.message : 'Could not load metrics'
        setError(msg)
        showToast('error', msg)
      })
      .finally(() => setLoading(false))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []) // intentional empty deps — load once

  return {
    data:    state.metricsCache,
    loading,
    error,
  }
}
