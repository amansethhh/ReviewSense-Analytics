import { useState, useCallback, useRef, useEffect } from 'react'
import { submitBulk, getBulkStatus, getBulkColumns,
  ApiClientError } from '@/api/api'
import { useApp } from '@/context/AppContext'
import type { BulkJobResult } from '@/types/api.types'

/**
 * BUG-3 FIX: Polling uses resp.job_id (local const from submit
 * response) directly in the closure — NOT useState which has
 * async updates. The poll chain uses setTimeout with the job_id
 * captured at submit time, ensuring no null-reference polls.
 *
 * Additional fix: catch handler no longer kills polling on
 * transient network errors. It logs the error and retries
 * next tick. Only permanent failures (3 consecutive errors)
 * stop polling.
 */
export function useBulk() {
  const { showToast } = useApp()
  const [jobId,    setJobId]    = useState<string | null>(null)
  const [result,   setResult]   = useState<BulkJobResult | null>(null)
  const [loading,  setLoading]  = useState(false)
  const [error,    setError]    = useState<string | null>(null)
  const [columns,  setColumns]  = useState<string[]>([])
  const [preview,  setPreview]  = useState<Record<string, unknown>[]>([])
  const pollRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const activeRef = useRef(false)
  const errorCountRef = useRef(0)

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      activeRef.current = false
      if (pollRef.current) clearTimeout(pollRef.current)
    }
  }, [])

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
    activeRef.current = true
    errorCountRef.current = 0
    try {
      const resp = await submitBulk(
        file, textColumn, model, runAbsa, runSarcasm, multilingual)
      // BUG-3 FIX: Use resp.job_id (local const) directly.
      // This is captured by the poll closure and is NEVER null
      // because it comes directly from the server response.
      const capturedJobId = resp.job_id
      setJobId(capturedJobId)

      // Polling loop: setTimeout chain prevents overlapping
      // requests. Uses capturedJobId (local const), not state.
      const poll = async () => {
        if (!activeRef.current) return
        try {
          const status = await getBulkStatus(capturedJobId)
          setResult(status)
          errorCountRef.current = 0  // reset on success
          if (status.status === 'completed' ||
              status.status === 'failed') {
            activeRef.current = false
            setLoading(false)
            if (status.status === 'completed') {
              showToast('success',
                `Analysis complete: ${status.processed
                } rows processed`)
            } else {
              showToast('error',
                `Job failed: ${status.error ?? 'Unknown'}`)
            }
            return // stop polling
          }
          // Schedule next poll — 500ms for near-real-time
          if (activeRef.current) {
            pollRef.current = setTimeout(poll, 500)
          }
        } catch (err) {
          // BUG-3 FIX: Don't kill polling on transient errors.
          // Log and retry. Only stop after 3 consecutive fails.
          errorCountRef.current += 1
          console.error(
            '[useBulk] Polling error '
            + `(${errorCountRef.current}/3):`, err)
          if (errorCountRef.current >= 3) {
            activeRef.current = false
            setLoading(false)
            showToast('error', 'Lost contact with server')
            return
          }
          // Retry with backoff
          if (activeRef.current) {
            pollRef.current = setTimeout(
              poll, 1000 * errorCountRef.current)
          }
        }
      }

      // Fire first poll immediately
      poll()
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
      activeRef.current = false
      showToast('error', msg)
    }
  }, [showToast])

  const reset = useCallback(() => {
    activeRef.current = false
    if (pollRef.current) clearTimeout(pollRef.current)
    errorCountRef.current = 0
    setJobId(null)
    setResult(null)
    setLoading(false)
    setError(null)
    setColumns([])
    setPreview([])
  }, [])

  return {
    jobId, result, loading, error, columns, preview,
    submit, reset, previewColumns,
  }
}
