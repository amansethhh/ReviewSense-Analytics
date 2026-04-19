/**
 * useLanguageStore — persists Language Analysis page state across navigation.
 *
 * Both tabs (single + batch) maintain independent state.
 * Tab switching does NOT clear either tab's state.
 *
 * Single tab reset: clears result, feedbackSent, selectedCorrection. Preserves text + settings.
 * Batch tab reset: clears bStage→'upload', bJobId, bResult, bStartedAt, bFileName. Preserves bModel.
 *
 * Timer fix (Phase 11): replaced `bElapsed` counter with `bStartedAt` timestamp.
 * Elapsed is now derived as Math.floor((Date.now() - bStartedAt) / 1000).
 */
import { useState, useCallback } from 'react'
import { usePageState } from '@/context/PageStateContext'
import type { LanguageResponse, BulkJobResult, ModelChoice, DomainChoice, SentimentLabel } from '@/types/api.types'

export function useLanguageStore() {
  const { langRef } = usePageState()
  const r = langRef.current

  // Single tab state
  const [tab,              _setTab]              = useState<'single' | 'batch'>(r.tab)
  const [text,             _setText]             = useState(r.text)
  const [model,            _setModel]            = useState<ModelChoice>(r.model)
  const [domain,           _setDomain]           = useState<DomainChoice>(r.domain)
  const [starRating,       _setStarRating]       = useState<number | null>(r.starRating)
  const [includeLime,      _setIncludeLime]      = useState(r.includeLime)
  const [includeAbsa,      _setIncludeAbsa]      = useState(r.includeAbsa)
  const [includeSarcasm,   _setIncludeSarcasm]   = useState(r.includeSarcasm)
  const [data,             _setData]             = useState<LanguageResponse | null>(r.data)
  const [feedbackSent,     _setFeedbackSent]     = useState(r.feedbackSent)
  const [selectedCorrection, _setSelectedCorrection] = useState<SentimentLabel | null>(r.selectedCorrection)

  // Batch tab state
  const [bFileName,       _setBFileName]       = useState<string | null>(r.bFileName)
  const [bTextCol,        _setBTextCol]        = useState(r.bTextCol)
  const [bModel,          _setBModel]          = useState(r.bModel)
  const [bRunAbsa,        _setBRunAbsa]        = useState(r.bRunAbsa)
  const [bRunSarcasm,     _setBRunSarcasm]     = useState(r.bRunSarcasm)
  const [bIsMultilingual, _setBIsMultilingual] = useState(r.bIsMultilingual)
  const [bShowAll,        _setBShowAll]        = useState(r.bShowAll)
  const [bStartedAt, _setBStartedAt] = useState<number | null>(r.bStartedAt)
  const [bStage,     _setBStage]     = useState<'upload' | 'configure' | 'processing' | 'results'>(r.bStage)
  const [bJobId,     _setBJobId]     = useState<string | null>(r.bJobId)
  const [bResult,    _setBResult]    = useState<BulkJobResult | null>(r.bResult)
  const [bColumns,   _setBColumns]   = useState<string[]>(r.bColumns)
  const [bPreview,   _setBPreview]   = useState<Record<string, unknown>[]>(r.bPreview)

  // Synced setters — single tab
  const setTab = useCallback((v: 'single' | 'batch') => {
    _setTab(v); langRef.current.tab = v
  }, [langRef])
  const setText = useCallback((v: string) => {
    _setText(v); langRef.current.text = v
  }, [langRef])
  const setModel = useCallback((v: ModelChoice) => {
    _setModel(v); langRef.current.model = v
  }, [langRef])
  const setDomain = useCallback((v: DomainChoice) => {
    _setDomain(v); langRef.current.domain = v
  }, [langRef])
  const setStarRating = useCallback((v: number | null) => {
    _setStarRating(v); langRef.current.starRating = v
  }, [langRef])
  const setIncludeLime = useCallback((v: boolean) => {
    _setIncludeLime(v); langRef.current.includeLime = v
  }, [langRef])
  const setIncludeAbsa = useCallback((v: boolean) => {
    _setIncludeAbsa(v); langRef.current.includeAbsa = v
  }, [langRef])
  const setIncludeSarcasm = useCallback((v: boolean) => {
    _setIncludeSarcasm(v); langRef.current.includeSarcasm = v
  }, [langRef])
  const setData = useCallback((v: LanguageResponse | null) => {
    _setData(v); langRef.current.data = v
  }, [langRef])
  const setFeedbackSent = useCallback((v: boolean) => {
    _setFeedbackSent(v); langRef.current.feedbackSent = v
  }, [langRef])
  const setSelectedCorrection = useCallback((v: SentimentLabel | null) => {
    _setSelectedCorrection(v); langRef.current.selectedCorrection = v
  }, [langRef])

  // Synced setters — batch tab
  const setBFileName = useCallback((v: string | null) => {
    _setBFileName(v); langRef.current.bFileName = v
  }, [langRef])
  const setBTextCol = useCallback((v: string) => {
    _setBTextCol(v); langRef.current.bTextCol = v
  }, [langRef])
  const setBModel = useCallback((v: string) => {
    _setBModel(v); langRef.current.bModel = v
  }, [langRef])
  const setBRunAbsa = useCallback((v: boolean) => {
    _setBRunAbsa(v); langRef.current.bRunAbsa = v
  }, [langRef])
  const setBRunSarcasm = useCallback((v: boolean) => {
    _setBRunSarcasm(v); langRef.current.bRunSarcasm = v
  }, [langRef])
  const setBIsMultilingual = useCallback((v: boolean) => {
    _setBIsMultilingual(v); langRef.current.bIsMultilingual = v
  }, [langRef])
  const setBShowAll = useCallback((v: boolean) => {
    _setBShowAll(v); langRef.current.bShowAll = v
  }, [langRef])
  const setBStartedAt = useCallback((v: number | null) => {
    _setBStartedAt(v); langRef.current.bStartedAt = v
  }, [langRef])
  const setBStage = useCallback((v: 'upload' | 'configure' | 'processing' | 'results') => {
    _setBStage(v); langRef.current.bStage = v
  }, [langRef])
  const setBJobId = useCallback((v: string | null) => {
    _setBJobId(v); langRef.current.bJobId = v
  }, [langRef])
  const setBResult = useCallback((v: BulkJobResult | null) => {
    _setBResult(v); langRef.current.bResult = v
  }, [langRef])
  const setBColumns = useCallback((v: string[]) => {
    _setBColumns(v); langRef.current.bColumns = v
  }, [langRef])
  const setBPreview = useCallback((v: Record<string, unknown>[]) => {
    _setBPreview(v); langRef.current.bPreview = v
  }, [langRef])

  /** Single tab reset: clears result + feedback, preserves form inputs */
  const resetSingle = useCallback(() => {
    setData(null)
    setFeedbackSent(false)
    setSelectedCorrection(null)
  }, [setData, setFeedbackSent, setSelectedCorrection])

  /** Batch tab reset: clears job state, preserves bModel preference */
  const resetBatch = useCallback(() => {
    setBStage('upload')
    setBFileName(null)
    setBTextCol('')
    setBJobId(null)
    setBResult(null)
    setBStartedAt(null)
    setBShowAll(false)
    setBColumns([])
    setBPreview([])
  }, [setBStage, setBFileName, setBTextCol, setBJobId, setBResult, setBStartedAt, setBShowAll, setBColumns, setBPreview])

  return {
    // Single tab
    tab, setTab, text, setText, model, setModel, domain, setDomain,
    starRating, setStarRating,
    includeLime, setIncludeLime, includeAbsa, setIncludeAbsa,
    includeSarcasm, setIncludeSarcasm,
    data, setData, feedbackSent, setFeedbackSent,
    selectedCorrection, setSelectedCorrection,
    resetSingle,
    // Batch tab
    bFileName, setBFileName, bTextCol, setBTextCol,
    bModel, setBModel, bRunAbsa, setBRunAbsa,
    bRunSarcasm, setBRunSarcasm, bIsMultilingual, setBIsMultilingual,
    bShowAll, setBShowAll,
    bStartedAt, setBStartedAt, bStage, setBStage,
    bJobId, setBJobId, bResult, setBResult,
    bColumns, setBColumns, bPreview, setBPreview,
    resetBatch,
  }
}
