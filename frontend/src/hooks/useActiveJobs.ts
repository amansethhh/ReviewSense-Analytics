/**
 * useActiveJobs — polls GET /bulk/active every 3 seconds.
 *
 * Used by the Sidebar nav bar indicator to show a pulsing dot
 * when any job is currently queued or processing.
 *
 * Features:
 * - Page Visibility API: pauses polling when browser tab is hidden
 * - Resumes immediately on tab focus (no stale data)
 * - Non-critical: silently swallows errors (indicator is best-effort)
 * - Separate 3000ms interval — does not interfere with 250ms job polls
 */
import { useState, useEffect, useRef } from 'react'
import { getActiveJobs } from '@/api/api'
import type { ActiveJob } from '@/api/api'

const POLL_MS = 3000

export function useActiveJobs(): ActiveJob[] {
  const [activeJobs, setActiveJobs] = useState<ActiveJob[]>([])
  const mountedRef = useRef(true)

  useEffect(() => {
    mountedRef.current = true
    let timerHandle: ReturnType<typeof setTimeout> | null = null

    const poll = async () => {
      if (!mountedRef.current) return

      // Page Visibility API: skip fetch when tab is hidden; resume on visible
      if (document.visibilityState !== 'hidden') {
        try {
          const data = await getActiveJobs()
          if (mountedRef.current) setActiveJobs(data.active_jobs)
        } catch {
          // Non-critical — silently ignore network errors
        }
      }

      if (mountedRef.current) {
        timerHandle = setTimeout(poll, POLL_MS)
      }
    }

    // Resume immediately when tab becomes visible again
    const handleVisibility = () => {
      if (document.visibilityState === 'visible' && mountedRef.current) {
        if (timerHandle) clearTimeout(timerHandle)
        poll()
      }
    }

    document.addEventListener('visibilitychange', handleVisibility)
    poll() // initial fetch

    return () => {
      mountedRef.current = false
      if (timerHandle) clearTimeout(timerHandle)
      document.removeEventListener('visibilitychange', handleVisibility)
    }
  }, [])

  return activeJobs
}
