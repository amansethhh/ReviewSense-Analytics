import { useState, useCallback } from 'react'
import { analyzeLanguage, ApiClientError } from '@/api/api'
import { useApp } from '@/context/AppContext'
import type { LanguageRequest, LanguageResponse }
  from '@/types/api.types'

export function useLanguage() {
  const { showToast } = useApp()
  const [data,    setData]    =
    useState<LanguageResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error,   setError]   = useState<string | null>(null)

  const run = useCallback(async (req: LanguageRequest) => {
    setLoading(true)
    setError(null)
    setData(null)
    try {
      const result = await analyzeLanguage(req)
      setData(result)
    } catch (err) {
      const msg =
        err instanceof ApiClientError
          ? err.data.detail ?? err.data.error
          : err instanceof TypeError &&
            err.message.includes('fetch')
          ? 'Cannot connect to the API. Is the backend running?'
          : err instanceof Error
          ? err.message
          : 'Language analysis failed'
      setError(msg)
      showToast('error', msg)
    } finally {
      setLoading(false)
    }
  }, [showToast])

  const reset = useCallback(() => {
    setData(null)
    setError(null)
  }, [])

  return { data, loading, error, run, reset }
}
