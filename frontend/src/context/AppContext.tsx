import React, {
  createContext, useContext, useReducer, useCallback
} from 'react'
import type { PredictResponse, MetricsResponse } from
  '@/types/api.types'

// ── State shape ─────────────────────────────────────

interface Toast {
  id:      string
  type:    'success' | 'error' | 'info'
  message: string
}

interface AppState {
  toasts:               Toast[]
  lastPrediction:       PredictResponse | null
  metricsCache:         MetricsResponse | null
  apiConnected:         boolean
  confidenceThreshold:  number
}

const initialState: AppState = {
  toasts:              [],
  lastPrediction:      null,
  metricsCache:        null,
  apiConnected:        true,
  confidenceThreshold: 0.60,
}

// ── Actions ─────────────────────────────────────────

type Action =
  | { type: 'ADD_TOAST';              payload: Toast }
  | { type: 'REMOVE_TOAST';           payload: string }
  | { type: 'SET_PREDICTION';         payload: PredictResponse }
  | { type: 'SET_METRICS';            payload: MetricsResponse }
  | { type: 'SET_API_STATUS';         payload: boolean }
  | { type: 'SET_CONF_THRESHOLD';     payload: number }

function reducer(state: AppState, action: Action):
  AppState {
  switch (action.type) {
    case 'ADD_TOAST':
      return {
        ...state,
        toasts: [...state.toasts, action.payload],
      }
    case 'REMOVE_TOAST':
      return {
        ...state,
        toasts: state.toasts.filter(
          t => t.id !== action.payload),
      }
    case 'SET_PREDICTION':
      return { ...state, lastPrediction: action.payload }
    case 'SET_METRICS':
      return { ...state, metricsCache: action.payload }
    case 'SET_API_STATUS':
      return { ...state, apiConnected: action.payload }
    case 'SET_CONF_THRESHOLD':
      return { ...state, confidenceThreshold: action.payload }
    default:
      return state
  }
}

// ── Context ─────────────────────────────────────────

interface AppContextValue {
  state:                  AppState
  dispatch:               React.Dispatch<Action>
  showToast:              (type: Toast['type'], message: string) => void
  setConfidenceThreshold: (v: number) => void
}

const AppContext = createContext<AppContextValue | null>(null)

export function AppProvider({
  children,
}: {
  children: React.ReactNode
}) {
  const [state, dispatch] = useReducer(reducer, initialState)

  const showToast = useCallback(
    (type: Toast['type'], message: string) => {
      const id = crypto.randomUUID()
      dispatch({ type: 'ADD_TOAST',
                 payload: { id, type, message } })
      setTimeout(() => {
        dispatch({ type: 'REMOVE_TOAST', payload: id })
      }, 4000)
    },
    [dispatch],
  )

  const setConfidenceThreshold = useCallback(
    (v: number) => dispatch({ type: 'SET_CONF_THRESHOLD', payload: v }),
    [dispatch],
  )

  return (
    <AppContext.Provider value={{ state, dispatch, showToast, setConfidenceThreshold }}>
      {children}
    </AppContext.Provider>
  )
}

export function useApp() {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error(
    'useApp must be used inside AppProvider')
  return ctx
}
