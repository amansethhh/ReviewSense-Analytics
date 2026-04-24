/**
 * useActiveJobs — polls GET /bulk/active for sidebar progress.
 *
 * Used by the Sidebar progress loader to show real-time pipeline
 * stages when any job is currently queued or processing.
 *
 * Features:
 * - ADAPTIVE POLLING: 1000ms when jobs are active (near-zero latency
 *   vs the analysis page's 500ms poller), 3000ms when idle.
 * - Page Visibility API: pauses polling when browser tab is hidden
 * - Resumes immediately on tab focus (no stale data)
 * - Non-critical: silently swallows errors (indicator is best-effort)
 */
import { useState, useEffect, useRef, useCallback } from 'react'
import { getActiveJobs } from '@/api/api'
import type { ActiveJob } from '@/api/api'

/** Idle poll — no jobs running, just checking periodically. */
const POLL_IDLE_MS = 3000
/** Active poll — jobs running, keep the sidebar in sync with the analysis page. */
const POLL_ACTIVE_MS = 1000

export function useActiveJobs(): ActiveJob[] {
  const [activeJobs, setActiveJobs] = useState<ActiveJob[]>([])
  const mountedRef = useRef(true)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const hasActiveRef = useRef(false)

  const poll = useCallback(async () => {
    if (!mountedRef.current) return

    // Page Visibility API: skip fetch when tab is hidden
    if (document.visibilityState !== 'hidden') {
      try {
        const data = await getActiveJobs()
        if (mountedRef.current) {
          const jobs = data.active_jobs
          setActiveJobs(jobs)
          hasActiveRef.current = jobs.length > 0
        }
      } catch {
        // Non-critical — silently ignore network errors
      }
    }

    if (mountedRef.current) {
      // Adaptive interval: fast when jobs active, slow when idle
      const interval = hasActiveRef.current ? POLL_ACTIVE_MS : POLL_IDLE_MS
      timerRef.current = setTimeout(poll, interval)
    }
  }, [])

  useEffect(() => {
    mountedRef.current = true

    // Resume immediately when tab becomes visible
    const handleVisibility = () => {
      if (document.visibilityState === 'visible' && mountedRef.current) {
        if (timerRef.current) clearTimeout(timerRef.current)
        poll()
      }
    }

    document.addEventListener('visibilitychange', handleVisibility)
    poll() // initial fetch

    return () => {
      mountedRef.current = false
      if (timerRef.current) clearTimeout(timerRef.current)
      document.removeEventListener('visibilitychange', handleVisibility)
    }
  }, [poll])

  return activeJobs
}
