// This is the ONLY file that calls fetch().
// Every route in every hook must import from here.
// Never call fetch() directly in a component or hook.

import type {
  PredictRequest, PredictResponse,
  BulkJobSubmitResponse, BulkJobResult,
  LanguageRequest, LanguageResponse,
  MetricsResponse, ApiError,
  LiveStatsResponse,
} from '@/types/api.types'

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

// ── Retry configuration ─────────────────────────────
const MAX_RETRIES   = 3
const BASE_DELAY_MS = 1000  // 1s → 2s → 4s (exponential)

class ApiClientError extends Error {
  constructor(
    public status: number,
    public data: ApiError,
    message: string,
  ) {
    super(message)
    this.name = 'ApiClientError'
  }
}

/** Delay helper for retry backoff */
function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms))
}

/**
 * Core fetch wrapper with automatic retry logic.
 *
 * Retries up to MAX_RETRIES on:
 *   - Network errors  (fetch throws)
 *   - 5xx server errors (backend is starting / crashed)
 *
 * Does NOT retry on:
 *   - 4xx client errors (bad request, auth, etc.)
 */
async function request<T>(
  path: string,
  options?: RequestInit,
): Promise<T> {
  const url = `${BASE_URL}${path}`
  let lastError: Error | null = null

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      const res = await fetch(url, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
      })

      // 4xx → throw immediately, no retry
      if (res.status >= 400 && res.status < 500) {
        const errData = await parseError(res)
        throw new ApiClientError(
          res.status, errData,
          errData.detail ?? errData.error,
        )
      }

      // 5xx → retry
      if (res.status >= 500) {
        const errData = await parseError(res)
        lastError = new ApiClientError(
          res.status, errData,
          errData.detail ?? errData.error,
        )
        if (attempt < MAX_RETRIES) {
          const wait = BASE_DELAY_MS * Math.pow(2, attempt)
          console.warn(
            `[API] ${path} → ${res.status}, retrying in ${wait}ms `
            + `(${attempt + 1}/${MAX_RETRIES})`,
          )
          await delay(wait)
          continue
        }
        throw lastError
      }

      // Success
      return res.json() as Promise<T>

    } catch (err) {
      // If it's already an ApiClientError with 4xx, don't retry
      if (err instanceof ApiClientError && err.status < 500) throw err

      lastError = err as Error

      if (attempt < MAX_RETRIES) {
        const wait = BASE_DELAY_MS * Math.pow(2, attempt)
        console.warn(
          `[API] ${path} → Network error, retrying in ${wait}ms `
          + `(${attempt + 1}/${MAX_RETRIES}):`,
          (err as Error).message,
        )
        await delay(wait)
      }
    }
  }

  // All retries exhausted
  throw lastError ?? new Error(`Request to ${path} failed after ${MAX_RETRIES} retries`)
}

/** Safely parse an error response body */
async function parseError(res: Response): Promise<ApiError> {
  try {
    return await res.json()
  } catch {
    return {
      error:  'Request failed',
      detail: res.statusText,
      code:   res.status,
    }
  }
}

// ── Predict ─────────────────────────────────────────

export async function predict(
  body: PredictRequest,
): Promise<PredictResponse> {
  return request<PredictResponse>('/predict', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

// ── Bulk ────────────────────────────────────────────

export async function submitBulk(
  file: File,
  textColumn: string,
  model: string,
  runAbsa: boolean,
  runSarcasm: boolean,
  multilingual: boolean = false,
): Promise<BulkJobSubmitResponse> {
  const form = new FormData()
  form.append('file', file)
  form.append('text_column', textColumn)
  form.append('model', model)
  form.append('run_absa', String(runAbsa))
  form.append('run_sarcasm', String(runSarcasm))
  form.append('multilingual', String(multilingual))

  // Do NOT set Content-Type header for FormData —
  // the browser sets it with the boundary automatically.
  const url = `${BASE_URL}/bulk`
  const res = await fetch(url, { method: 'POST', body: form })
  if (!res.ok) {
    const errData = await res.json().catch(() => ({
      error: 'Upload failed', detail: res.statusText,
      code: res.status,
    }))
    throw new ApiClientError(res.status, errData as ApiError,
      (errData as ApiError).detail ?? (errData as ApiError).error)
  }
  return res.json()
}

export async function getBulkStatus(
  jobId: string,
): Promise<BulkJobResult> {
  return request<BulkJobResult>(`/bulk/status/${jobId}`)
}

export async function getBulkColumns(
  file: File,
): Promise<{ columns: string[]; preview: Record<string, unknown>[] }> {
  // Parse CSV header + preview rows client-side.
  // The backend's /bulk/columns is @router.get with UploadFile
  // which browsers can't call (GET + body is not supported).
  const text = await file.text()
  const lines = text.split('\n').filter(l => l.trim())
  if (lines.length === 0) throw new Error('Empty file')

  // Parse header
  const headers = lines[0].split(',').map(h => h.trim().replace(/^"|"$/g, ''))

  // Parse up to 5 preview rows
  const preview: Record<string, unknown>[] = []
  for (let i = 1; i < Math.min(lines.length, 6); i++) {
    const vals = lines[i].match(/(".*?"|[^,]+)/g) ?? []
    const row: Record<string, unknown> = {}
    headers.forEach((h, j) => {
      row[h] = (vals[j] ?? '').trim().replace(/^"|"$/g, '')
    })
    preview.push(row)
  }

  return { columns: headers, preview }
}

// ── Language ────────────────────────────────────────

export async function analyzeLanguage(
  body: LanguageRequest,
): Promise<LanguageResponse> {
  return request<LanguageResponse>('/language', {
    method: 'POST',
    body: JSON.stringify(body),
  })
}

// ── Metrics ─────────────────────────────────────────

export async function getMetrics(): Promise<MetricsResponse> {
  return request<MetricsResponse>('/metrics')
}

// ── Live Stats ──────────────────────────────────────

export async function getLiveStats(): Promise<LiveStatsResponse> {
  return request<LiveStatsResponse>('/metrics/live')
}

// ── Active Jobs ─────────────────────────────────────

export interface ActiveJob {
  job_id:     string
  page:       'bulk' | 'language'
  status:     'queued' | 'processing'
  processed:  number
  total:      number
  phase:      string
  progress:   number
  created_at: string
}

export async function getActiveJobs(): Promise<{ active_jobs: ActiveJob[] }> {
  return request<{ active_jobs: ActiveJob[] }>('/bulk/active')
}

// ── Health ──────────────────────────────────────────

export async function getHealth(): Promise<{
  status: string
  models_loaded: boolean
  version: string
}> {
  return request('/health')
}

export { ApiClientError }
