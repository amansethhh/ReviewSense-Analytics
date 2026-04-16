import { useState, useCallback } from 'react'
import { predict as apiPredict, ApiClientError } from '@/api/api'
import { useApp } from '@/context/AppContext'
import type { PredictRequest, PredictResponse }
  from '@/types/api.types'

interface UsePredictState {
  data:    PredictResponse | null
  loading: boolean
  error:   string | null
}

export function usePredict() {
  const { dispatch, showToast } = useApp()
  const [state, setState] = useState<UsePredictState>({
    data: null, loading: false, error: null,
  })

  const run = useCallback(async (req: PredictRequest) => {
    setState({ data: null, loading: true, error: null })
    try {
      const result = await apiPredict(req)
      setState({ data: result, loading: false, error: null })
      dispatch({ type: 'SET_PREDICTION', payload: result })
    } catch (err) {
      const msg =
        err instanceof ApiClientError
          ? err.data.detail ?? err.data.error
          : err instanceof TypeError &&
            err.message.includes('fetch')
          ? 'Cannot connect to the API. Is the backend running?'
          : err instanceof Error
          ? err.message
          : 'Prediction failed'
      setState({ data: null, loading: false, error: msg })
      showToast('error', msg)
    }
  }, [dispatch, showToast])

  const reset = useCallback(() => {
    setState({ data: null, loading: false, error: null })
  }, [])

  return { ...state, run, reset }
}
