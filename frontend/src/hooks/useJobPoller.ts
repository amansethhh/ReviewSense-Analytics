/**
 * useJobPoller — module-level singleton poll registry.
 *
 * Manages all active bulk job poll loops from a single registry.
 * Prevents duplicate intervals if the same jobId is started twice.
 * Survives component unmount — polling continues across navigation.
 *
 * Usage:
 *   jobPoller.start({ jobId, onUpdate, onComplete, onError })
 *   jobPoller.stop(jobId)          // explicit stop (reset / cancel)
 *   jobPoller.stopAll()            // full reset (not normally needed)
 *   jobPoller.isPolling(jobId)     // query registry state
 */
import { getBulkStatus } from '@/api/api'
import type { BulkJobResult } from '@/types/api.types'

export interface PollJob {
  jobId:      string
  onUpdate:   (data: BulkJobResult) => void
  onComplete: (data: BulkJobResult) => void
  onError:    (message: string) => void
}

/** Module-level registry: jobId → active timeout handle */
const _registry  = new Map<string, ReturnType<typeof setTimeout>>()
const _errCounts = new Map<string, number>()

function start(job: PollJob): void {
  const { jobId, onUpdate, onComplete, onError } = job

  // Guard: if already polling this jobId, do nothing
  if (_registry.has(jobId)) return

  const poll = async (): Promise<void> => {
    // Aborted externally (stop() called between schedule and execution)
    if (!_registry.has(jobId)) return

    try {
      const status = await getBulkStatus(jobId)
      onUpdate(status)
      _errCounts.set(jobId, 0)

      if (status.status === 'completed' || status.status === 'failed') {
        _registry.delete(jobId)
        _errCounts.delete(jobId)
        if (status.status === 'completed') {
          onComplete(status)
        } else {
          onError(status.error ?? 'Job failed')
        }
        return
      }

      // Schedule next poll — 1000ms reduces re-render load vs 500ms
      // while still providing responsive progress updates.
      if (_registry.has(jobId)) {
        _registry.set(jobId, setTimeout(poll, 1000))
      }
    } catch {
      const count = (_errCounts.get(jobId) ?? 0) + 1
      _errCounts.set(jobId, count)
      console.error(`[jobPoller] Poll error for ${jobId.slice(0, 8)} (${count}/3)`)

      if (count >= 3) {
        _registry.delete(jobId)
        _errCounts.delete(jobId)
        onError('Lost contact with server')
        return
      }
      // Exponential backoff retry
      if (_registry.has(jobId)) {
        _registry.set(jobId, setTimeout(poll, 1000 * count))
      }
    }
  }

  // Register immediately with an imminent timeout (0ms fires after current call stack)
  _registry.set(jobId, setTimeout(poll, 0))
}

function stop(jobId: string): void {
  const handle = _registry.get(jobId)
  if (handle !== undefined) {
    clearTimeout(handle)
  }
  _registry.delete(jobId)
  _errCounts.delete(jobId)
}

function stopAll(): void {
  for (const handle of _registry.values()) {
    clearTimeout(handle)
  }
  _registry.clear()
  _errCounts.clear()
}

function isPolling(jobId: string): boolean {
  return _registry.has(jobId)
}

export const jobPoller = { start, stop, stopAll, isPolling }
