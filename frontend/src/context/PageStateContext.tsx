/**
 * PageStateContext — in-memory ref-backed store for page state persistence.
 *
 * Survives route navigation (Context is never unmounted).
 * Resets on browser refresh (in-memory, not persisted to storage).
 *
 * Each page gets a MutableRefObject holding its full state snapshot.
 * Page store hooks (usePredictStore, useBulkStore, etc.) read from these
 * refs on mount and write back on every state change. Because refs don't
 * trigger re-renders, the App shell is unaffected by page-level state churn.
 */
import { createContext, useContext, useRef } from 'react'
import type {
  ModelChoice, DomainChoice, SentimentLabel,
  PredictResponse, LanguageResponse, BulkJobResult,
  MetricsResponse,
} from '@/types/api.types'

/* ─── Per-page State Shapes ─────────────────────────── */

export interface PredictPageState {
  text: string
  model: ModelChoice
  domain: DomainChoice
  starRating: number | null
  includeLime: boolean
  includeAbsa: boolean
  includeSarcasm: boolean
  data: PredictResponse | null
  feedbackSent: boolean
  selectedCorrection: SentimentLabel | null
  serverError: string | null
}

export interface BulkPageState {
  stage: 'upload' | 'configure' | 'processing' | 'results'
  fileName: string | null          // display-only (File objects can't be ref'd)
  textColumn: string
  model: string
  runAbsa: boolean
  runSarcasm: boolean
  isMultilingual: boolean
  showAll: boolean
  startedAt: number | null         // Date.now() when processing began — survives navigation
  logs: string[]
  jobId: string | null
  result: BulkJobResult | null
  columns: string[]
  preview: Record<string, unknown>[]
}

export interface LangPageState {
  /* Single-analysis tab */
  tab: 'single' | 'batch'
  text: string
  model: ModelChoice
  domain: DomainChoice
  starRating: number | null
  includeLime: boolean
  includeAbsa: boolean
  includeSarcasm: boolean
  data: LanguageResponse | null
  feedbackSent: boolean
  selectedCorrection: SentimentLabel | null
  /* Batch tab */
  bFileName: string | null
  bTextCol: string
  bModel: string
  bRunAbsa: boolean
  bRunSarcasm: boolean
  bShowAll: boolean
  bStartedAt: number | null         // Date.now() when batch processing began
  bStage: 'upload' | 'configure' | 'processing' | 'results'
  bJobId: string | null
  bResult: BulkJobResult | null
  bColumns: string[]
  bPreview: Record<string, unknown>[]
}

export interface DashboardPageState {
  sortKey: string
  sortDir: 'asc' | 'desc'
  metricsSnapshot: MetricsResponse | null
}

/* ─── Defaults ──────────────────────────────────────── */

export const PREDICT_DEFAULTS: PredictPageState = {
  text: '', model: 'best', domain: 'all', starRating: null,
  includeLime: true, includeAbsa: true, includeSarcasm: true,
  data: null, feedbackSent: false, selectedCorrection: null,
  serverError: null,
}

export const BULK_DEFAULTS: BulkPageState = {
  stage: 'upload', fileName: null, textColumn: '', model: 'best',
  runAbsa: false, runSarcasm: true, isMultilingual: false,
  showAll: false, startedAt: null, logs: [], jobId: null, result: null,
  columns: [], preview: [],
}

export const LANG_DEFAULTS: LangPageState = {
  tab: 'single',
  text: '', model: 'best', domain: 'all', starRating: null,
  includeLime: true, includeAbsa: true, includeSarcasm: true,
  data: null, feedbackSent: false, selectedCorrection: null,
  bFileName: null, bTextCol: '', bModel: 'best',
  bRunAbsa: false, bRunSarcasm: true, bShowAll: false,
  bStartedAt: null, bStage: 'upload', bJobId: null, bResult: null,
  bColumns: [], bPreview: [],
}

export const DASHBOARD_DEFAULTS: DashboardPageState = {
  sortKey: 'accuracy', sortDir: 'desc', metricsSnapshot: null,
}

/* ─── Context Value ─────────────────────────────────── */

interface PageStateContextValue {
  predictRef:   React.MutableRefObject<PredictPageState>
  bulkRef:      React.MutableRefObject<BulkPageState>
  langRef:      React.MutableRefObject<LangPageState>
  dashboardRef: React.MutableRefObject<DashboardPageState>
}

const PageStateCtx = createContext<PageStateContextValue | null>(null)

/* ─── Provider ──────────────────────────────────────── */

export function PageStateProvider({ children }: { children: React.ReactNode }) {
  const predictRef   = useRef<PredictPageState>({ ...PREDICT_DEFAULTS })
  const bulkRef      = useRef<BulkPageState>({ ...BULK_DEFAULTS })
  const langRef      = useRef<LangPageState>({ ...LANG_DEFAULTS })
  const dashboardRef = useRef<DashboardPageState>({ ...DASHBOARD_DEFAULTS })

  return (
    <PageStateCtx.Provider value={{ predictRef, bulkRef, langRef, dashboardRef }}>
      {children}
    </PageStateCtx.Provider>
  )
}

/* ─── Hook ──────────────────────────────────────────── */

export function usePageState() {
  const ctx = useContext(PageStateCtx)
  if (!ctx) throw new Error('usePageState must be used inside PageStateProvider')
  return ctx
}
