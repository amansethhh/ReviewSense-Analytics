import { useState, useCallback } from 'react'
import { submitBulk, getBulkColumns, ApiClientError } from '@/api/api'
import { useApp } from '@/context/AppContext'
import { jobPoller } from '@/hooks/useJobPoller'
import type { BulkJobResult } from '@/types/api.types'

/**
 * useBulk — bulk job submission + polling, now backed by jobPoller singleton.
 *
 * Key changes from Phase 10:
 * - submit() / resumePolling() delegate to jobPoller.start() instead of
 *   maintaining their own setTimeout chains.
 * - Polling survives component unmount (no cleanup on unmount).
 * - reset() calls jobPoller.stop(jobId) to cancel an active poll.
 * - resumePolling() calls jobPoller.stop() before start() to replace
 *   stale callbacks from a previous mount with fresh ones.
 *
 * Two simultaneous jobs (Bulk + Language Batch) each call jobPoller.start()
 * with different jobIds → the singleton registry keeps them isolated.
 */
export function useBulk() {
  const { showToast } = useApp()
  const [jobId,   setJobId]   = useState<string | null>(null)
  const [result,  setResult]  = useState<BulkJobResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState<string | null>(null)
  const [columns, setColumns] = useState<string[]>([])
  const [preview, setPreview] = useState<Record<string, unknown>[]>([])

  // Note: NO cleanup useEffect on unmount.
  // jobPoller is a singleton — polling intentionally survives navigation.
  // The user's job runs in the background until complete or reset() is called.

  const previewColumns = useCallback(async (file: File) => {
    try {
      const data = await getBulkColumns(file)
      setColumns(data.columns)
      setPreview(data.preview ?? [])
      return data.columns
    } catch {
      showToast('error', 'Could not read CSV columns')
      return []
    }
  }, [showToast])

  const submit = useCallback(async (
    file: File,
    textColumn: string,
    model: string,
    runAbsa: boolean,
    runSarcasm: boolean,
    multilingual: boolean = false,
  ) => {
    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const resp = await submitBulk(
        file, textColumn, model, runAbsa, runSarcasm, multilingual)
      const capturedJobId = resp.job_id
      setJobId(capturedJobId)

      jobPoller.start({
        jobId: capturedJobId,
        onUpdate: (status) => setResult(status),
        onComplete: (status) => {
          setResult(status)
          setLoading(false)
          showToast('success',
            `Analysis complete: ${status.processed} rows processed`)
        },
        onError: (msg) => {
          setLoading(false)
          setError(msg)
          showToast('error', msg)
        },
      })
    } catch (err) {
      const msg =
        err instanceof ApiClientError
          ? err.data.detail ?? err.data.error
          : err instanceof TypeError &&
            err.message.includes('fetch')
          ? 'Cannot connect to the API. Is the backend running?'
          : err instanceof Error
          ? err.message
          : 'Upload failed'
      setError(msg)
      setLoading(false)
      showToast('error', msg)
    }
  }, [showToast])

  /**
   * Resume polling for an existing job (e.g. after navigating back).
   * Stops any stale poll (old callbacks from previous mount) before
   * starting fresh with the current hook instance's callbacks.
   */
  const resumePolling = useCallback((existingJobId: string) => {
    // Stop stale poll (if still running from previous mount)
    jobPoller.stop(existingJobId)

    setJobId(existingJobId)
    setLoading(true)
    setError(null)

    jobPoller.start({
      jobId: existingJobId,
      onUpdate: (status) => setResult(status),
      onComplete: (status) => {
        setResult(status)
        setLoading(false)
        showToast('success',
          `Analysis complete: ${status.processed} rows processed`)
      },
      onError: (msg) => {
        setLoading(false)
        setError(msg)
        showToast('error', msg)
      },
    })
  }, [showToast])

  const reset = useCallback(() => {
    // Stop any active poll for the current job
    if (jobId) jobPoller.stop(jobId)
    setJobId(null)
    setResult(null)
    setLoading(false)
    setError(null)
    setColumns([])
    setPreview([])
  }, [jobId])

  return {
    jobId, result, loading, error, columns, preview,
    submit, reset, previewColumns, resumePolling,
  }
}
