/**
 * usePredictStore — persists Live Prediction page state across navigation.
 *
 * Reads from PageStateContext ref on mount.
 * Writes back on every state change.
 *
 * reset() clears: result, feedbackSent, selectedCorrection
 * reset() preserves: text, model, domain, starRating, toggles
 */
import { useState, useCallback } from 'react'
import { usePageState, PREDICT_DEFAULTS } from '@/context/PageStateContext'
import type { PredictResponse, ModelChoice, DomainChoice, SentimentLabel } from '@/types/api.types'

export function usePredictStore() {
  const { predictRef } = usePageState()
  const r = predictRef.current

  // Initialize from ref (survives navigation)
  const [text,       _setText]       = useState(r.text)
  const [model,      _setModel]      = useState<ModelChoice>(r.model)
  const [domain,     _setDomain]     = useState<DomainChoice>(r.domain)
  const [starRating, _setStarRating] = useState<number | null>(r.starRating)
  const [includeLime,    _setIncludeLime]    = useState(r.includeLime)
  const [includeAbsa,    _setIncludeAbsa]    = useState(r.includeAbsa)
  const [includeSarcasm, _setIncludeSarcasm] = useState(r.includeSarcasm)
  const [data,       _setData]       = useState<PredictResponse | null>(r.data)
  const [feedbackSent, _setFeedbackSent] = useState(r.feedbackSent)
  const [selectedCorrection, _setSelectedCorrection] = useState<SentimentLabel | null>(r.selectedCorrection)
  const [serverError, _setServerError] = useState<string | null>(r.serverError)

  // Wrapped setters: update local state + ref
  const setText = useCallback((v: string) => {
    _setText(v); predictRef.current.text = v
  }, [predictRef])
  const setModel = useCallback((v: ModelChoice) => {
    _setModel(v); predictRef.current.model = v
  }, [predictRef])
  const setDomain = useCallback((v: DomainChoice) => {
    _setDomain(v); predictRef.current.domain = v
  }, [predictRef])
  const setStarRating = useCallback((v: number | null) => {
    _setStarRating(v); predictRef.current.starRating = v
  }, [predictRef])
  const setIncludeLime = useCallback((v: boolean) => {
    _setIncludeLime(v); predictRef.current.includeLime = v
  }, [predictRef])
  const setIncludeAbsa = useCallback((v: boolean) => {
    _setIncludeAbsa(v); predictRef.current.includeAbsa = v
  }, [predictRef])
  const setIncludeSarcasm = useCallback((v: boolean) => {
    _setIncludeSarcasm(v); predictRef.current.includeSarcasm = v
  }, [predictRef])
  const setData = useCallback((v: PredictResponse | null) => {
    _setData(v); predictRef.current.data = v
  }, [predictRef])
  const setFeedbackSent = useCallback((v: boolean) => {
    _setFeedbackSent(v); predictRef.current.feedbackSent = v
  }, [predictRef])
  const setSelectedCorrection = useCallback((v: SentimentLabel | null) => {
    _setSelectedCorrection(v); predictRef.current.selectedCorrection = v
  }, [predictRef])
  const setServerError = useCallback((v: string | null) => {
    _setServerError(v); predictRef.current.serverError = v
  }, [predictRef])

  /** Reset: clears result + feedback + serverError, preserves form inputs */
  const reset = useCallback(() => {
    setData(null)
    setFeedbackSent(false)
    setSelectedCorrection(null)
    setServerError(null)
  }, [setData, setFeedbackSent, setSelectedCorrection, setServerError])

  /** Full reset: everything back to defaults */
  const fullReset = useCallback(() => {
    Object.assign(predictRef.current, { ...PREDICT_DEFAULTS })
    _setText(PREDICT_DEFAULTS.text)
    _setModel(PREDICT_DEFAULTS.model)
    _setDomain(PREDICT_DEFAULTS.domain)
    _setStarRating(PREDICT_DEFAULTS.starRating)
    _setIncludeLime(PREDICT_DEFAULTS.includeLime)
    _setIncludeAbsa(PREDICT_DEFAULTS.includeAbsa)
    _setIncludeSarcasm(PREDICT_DEFAULTS.includeSarcasm)
    _setData(null)
    _setFeedbackSent(false)
    _setSelectedCorrection(null)
  }, [predictRef])

  return {
    text, setText, model, setModel, domain, setDomain,
    starRating, setStarRating,
    includeLime, setIncludeLime, includeAbsa, setIncludeAbsa,
    includeSarcasm, setIncludeSarcasm,
    data, setData, feedbackSent, setFeedbackSent,
    selectedCorrection, setSelectedCorrection,
    serverError, setServerError,
    reset, fullReset,
  }
}
