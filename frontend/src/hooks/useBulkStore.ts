/**
 * useBulkStore — persists Bulk Analysis page state across navigation.
 *
 * reset() clears: stage→'upload', jobId, result, logs, startedAt, fileName, columns, preview
 * reset() preserves: model, runAbsa, runSarcasm, isMultilingual (user preferences)
 *
 * Timer fix (Phase 11): replaced `elapsed` counter (froze on unmount)
 * with `startedAt` timestamp. Elapsed is now derived as
 * Math.floor((Date.now() - startedAt) / 1000) — always accurate.
 *
 * File Object note: File objects cannot be persisted in refs (they're opaque).
 * Only `fileName` (string) is stored for display. If the user returns to
 * 'configure' stage without a file, the UX shows a re-upload notice.
 */
import { useState, useCallback } from 'react'
import { usePageState, BULK_DEFAULTS } from '@/context/PageStateContext'
import type { BulkJobResult } from '@/types/api.types'

export function useBulkStore() {
  const { bulkRef } = usePageState()
  const r = bulkRef.current

  const [stage,          _setStage]          = useState<'upload' | 'configure' | 'processing' | 'results'>(r.stage)
  const [fileName,       _setFileName]       = useState<string | null>(r.fileName)
  const [textColumn,     _setTextColumn]     = useState(r.textColumn)
  const [model,          _setModel]          = useState(r.model)
  const [runAbsa,        _setRunAbsa]        = useState(r.runAbsa)
  const [runSarcasm,     _setRunSarcasm]     = useState(r.runSarcasm)
  const [isMultilingual, _setIsMultilingual] = useState(r.isMultilingual)
  const [showAll,        _setShowAll]        = useState(r.showAll)
  const [startedAt,      _setStartedAt]      = useState<number | null>(r.startedAt)
  const [logs,           _setLogs]           = useState<string[]>(r.logs)
  const [jobId,          _setJobId]          = useState<string | null>(r.jobId)
  const [result,         _setResult]         = useState<BulkJobResult | null>(r.result)
  const [columns,        _setColumns]        = useState<string[]>(r.columns)
  const [preview,        _setPreview]        = useState<Record<string, unknown>[]>(r.preview)

  // Synced setters
  const setStage = useCallback((v: 'upload' | 'configure' | 'processing' | 'results') => {
    _setStage(v); bulkRef.current.stage = v
  }, [bulkRef])
  const setFileName = useCallback((v: string | null) => {
    _setFileName(v); bulkRef.current.fileName = v
  }, [bulkRef])
  const setTextColumn = useCallback((v: string) => {
    _setTextColumn(v); bulkRef.current.textColumn = v
  }, [bulkRef])
  const setModel = useCallback((v: string) => {
    _setModel(v); bulkRef.current.model = v
  }, [bulkRef])
  const setRunAbsa = useCallback((v: boolean) => {
    _setRunAbsa(v); bulkRef.current.runAbsa = v
  }, [bulkRef])
  const setRunSarcasm = useCallback((v: boolean) => {
    _setRunSarcasm(v); bulkRef.current.runSarcasm = v
  }, [bulkRef])
  const setIsMultilingual = useCallback((v: boolean) => {
    _setIsMultilingual(v); bulkRef.current.isMultilingual = v
  }, [bulkRef])
  const setShowAll = useCallback((v: boolean) => {
    _setShowAll(v); bulkRef.current.showAll = v
  }, [bulkRef])
  const setStartedAt = useCallback((v: number | null) => {
    _setStartedAt(v); bulkRef.current.startedAt = v
  }, [bulkRef])
  const setLogs = useCallback((v: string[] | ((prev: string[]) => string[])) => {
    _setLogs(prev => {
      const next = typeof v === 'function' ? v(prev) : v
      bulkRef.current.logs = next
      return next
    })
  }, [bulkRef])
  const setJobId = useCallback((v: string | null) => {
    _setJobId(v); bulkRef.current.jobId = v
  }, [bulkRef])
  const setResult = useCallback((v: BulkJobResult | null) => {
    _setResult(v); bulkRef.current.result = v
  }, [bulkRef])
  const setColumns = useCallback((v: string[]) => {
    _setColumns(v); bulkRef.current.columns = v
  }, [bulkRef])
  const setPreview = useCallback((v: Record<string, unknown>[]) => {
    _setPreview(v); bulkRef.current.preview = v
  }, [bulkRef])

  /** Reset: clears job state, preserves user preferences */
  const reset = useCallback(() => {
    setStage('upload')
    setFileName(null)
    setTextColumn('')
    setJobId(null)
    setResult(null)
    setLogs([])
    setStartedAt(null)
    setShowAll(false)
    setColumns([])
    setPreview([])
  }, [setStage, setFileName, setTextColumn, setJobId, setResult, setLogs, setStartedAt, setShowAll, setColumns, setPreview])

  /** Full reset: everything back to defaults */
  const fullReset = useCallback(() => {
    Object.assign(bulkRef.current, { ...BULK_DEFAULTS })
    _setStage(BULK_DEFAULTS.stage)
    _setFileName(null)
    _setTextColumn('')
    _setModel(BULK_DEFAULTS.model)
    _setRunAbsa(BULK_DEFAULTS.runAbsa)
    _setRunSarcasm(BULK_DEFAULTS.runSarcasm)
    _setIsMultilingual(BULK_DEFAULTS.isMultilingual)
    _setShowAll(false)
    _setStartedAt(null)
    _setLogs([])
    _setJobId(null)
    _setResult(null)
    _setColumns([])
    _setPreview([])
  }, [bulkRef])

  return {
    stage, setStage, fileName, setFileName, textColumn, setTextColumn,
    model, setModel, runAbsa, setRunAbsa, runSarcasm, setRunSarcasm,
    isMultilingual, setIsMultilingual, showAll, setShowAll,
    startedAt, setStartedAt, logs, setLogs,
    jobId, setJobId, result, setResult,
    columns, setColumns, preview, setPreview,
    reset, fullReset,
  }
}
