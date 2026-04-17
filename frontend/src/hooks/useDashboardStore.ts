/**
 * useDashboardStore — persists Model Dashboard page state across navigation.
 *
 * On remount: if metricsSnapshot exists, render it immediately (no loading flash).
 * useMetrics will still re-fetch in the background via AppContext's metricsCache.
 */
import { useState, useCallback } from 'react'
import { usePageState } from '@/context/PageStateContext'
import type { MetricsResponse } from '@/types/api.types'

type SortKey = 'accuracy' | 'macro_f1' | 'weighted_f1' | 'macro_prec' | 'auc' | 'train_time_s'

export function useDashboardStore() {
  const { dashboardRef } = usePageState()
  const r = dashboardRef.current

  const [sortKey, _setSortKey] = useState<SortKey>(r.sortKey as SortKey)
  const [sortDir, _setSortDir] = useState<'asc' | 'desc'>(r.sortDir)
  const [metricsSnapshot, _setMetricsSnapshot] = useState<MetricsResponse | null>(r.metricsSnapshot)

  const setSortKey = useCallback((v: SortKey) => {
    _setSortKey(v); dashboardRef.current.sortKey = v
  }, [dashboardRef])
  const setSortDir = useCallback((v: 'asc' | 'desc') => {
    _setSortDir(v); dashboardRef.current.sortDir = v
  }, [dashboardRef])
  const setMetricsSnapshot = useCallback((v: MetricsResponse | null) => {
    _setMetricsSnapshot(v); dashboardRef.current.metricsSnapshot = v
  }, [dashboardRef])

  const toggleSort = useCallback((key: SortKey) => {
    if (sortKey === key) {
      const next = sortDir === 'desc' ? 'asc' : 'desc'
      setSortDir(next)
    } else {
      setSortKey(key)
      setSortDir('desc')
    }
  }, [sortKey, sortDir, setSortKey, setSortDir])

  return {
    sortKey, setSortKey, sortDir, setSortDir,
    metricsSnapshot, setMetricsSnapshot,
    toggleSort,
  }
}
