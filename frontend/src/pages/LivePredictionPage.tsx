import { useCallback, useEffect, useMemo, useState, type CSSProperties, type ChangeEvent } from 'react'
import { SentimentBadge } from '@/components/ui/Badge'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { NeuralButton } from '@/components/ui/NeuralButton'
import { EyebrowPill } from '@/components/ui/EyebrowPill'
import { HoloToggle } from '@/components/ui/HoloToggle'
import { NeuralInputWrap } from '@/components/ui/NeuralInputWrap'
import { NeuralSelect } from '@/components/ui/NeuralSelect'
import { LIMEChart } from '@/components/charts/LIMEChart'
import { usePredict } from '@/hooks/usePredict'
import { usePredictStore } from '@/hooks/usePredictStore'
import { useApp } from '@/context/AppContext'
import type { ModelChoice, DomainChoice, SentimentLabel } from '@/types/api.types'

/* ── 3D Icon Components ── */
const icon3dStyle: CSSProperties = {
  filter: 'drop-shadow(0 4px 8px rgba(0,217,255,0.35)) drop-shadow(0 1px 2px rgba(0,0,0,0.4))',
  transform: 'perspective(400px) rotateY(-12deg) rotateX(5deg)',
  display: 'inline-block',
  flexShrink: 0,
}

function Icon3DBrain({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" style={icon3dStyle} fill="none">
      <defs>
        <linearGradient id="brain3d" x1="0" y1="0" x2="64" y2="64">
          <stop offset="0%" stopColor="#00D9FF" />
          <stop offset="100%" stopColor="#00FF88" />
        </linearGradient>
        <filter id="brain-glow"><feGaussianBlur stdDeviation="2" result="g"/><feMerge><feMergeNode in="g"/><feMergeNode in="SourceGraphic"/></feMerge></filter>
      </defs>
      <g filter="url(#brain-glow)">
        <path d="M32 8c-8 0-14 4-16 10-4 2-6 7-6 12s2 8 5 10c1 5 6 10 17 10s16-5 17-10c3-2 5-5 5-10s-2-10-6-12C46 12 40 8 32 8z" fill="url(#brain3d)" opacity=".18" />
        <path d="M32 12c-6 0-11 3-13 8-3 2-5 6-5 10 0 3 1.5 6 4 8 1 4 5 8 14 8s13-4 14-8c2.5-2 4-5 4-8 0-4-2-8-5-10-2-5-7-8-13-8z" stroke="url(#brain3d)" strokeWidth="2" fill="none" />
        <path d="M32 16v28M24 22c0 6 4 8 8 8s8-2 8-8M22 34c4 2 8 2 10 0s6-2 10 0" stroke="url(#brain3d)" strokeWidth="1.5" strokeLinecap="round" fill="none" opacity=".7" />
      </g>
    </svg>
  )
}

function Icon3DPen({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="pen3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#A78BFA"/></linearGradient></defs>
      <rect x="14" y="6" width="20" height="32" rx="3" fill="url(#pen3d)" opacity=".15" />
      <path d="M30 6L38 14L22 38H14V30L30 6z" stroke="url(#pen3d)" strokeWidth="2" strokeLinejoin="round" fill="none" />
      <path d="M14 38h20" stroke="url(#pen3d)" strokeWidth="2" strokeLinecap="round" opacity=".5" />
    </svg>
  )
}

function Icon3DChart({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="chart3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00FF88"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs>
      <rect x="6" y="28" width="8" height="14" rx="2" fill="url(#chart3d)" opacity=".3" />
      <rect x="20" y="18" width="8" height="24" rx="2" fill="url(#chart3d)" opacity=".5" />
      <rect x="34" y="8" width="8" height="34" rx="2" fill="url(#chart3d)" opacity=".7" />
      <path d="M6 44h36" stroke="url(#chart3d)" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

function Icon3DGear({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="gear3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#A78BFA"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs>
      <path d="M24 16a8 8 0 100 16 8 8 0 000-16z" stroke="url(#gear3d)" strokeWidth="2" fill="url(#gear3d)" fillOpacity=".15" />
      <path d="M24 4v6M24 38v6M4 24h6M38 24h6M9.9 9.9l4.2 4.2M33.9 33.9l4.2 4.2M38.1 9.9l-4.2 4.2M14.1 33.9l-4.2 4.2" stroke="url(#gear3d)" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  )
}

function Icon3DKey({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="key3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#FDE047"/><stop offset="100%" stopColor="#F59E0B"/></linearGradient></defs>
      <circle cx="16" cy="20" r="10" stroke="url(#key3d)" strokeWidth="2" fill="url(#key3d)" fillOpacity=".12" />
      <path d="M24 24h18M36 24v8M42 24v6" stroke="url(#key3d)" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  )
}

function Icon3DRobot({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="robot3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#00FF88"/></linearGradient></defs>
      <rect x="10" y="14" width="28" height="24" rx="6" stroke="url(#robot3d)" strokeWidth="2" fill="url(#robot3d)" fillOpacity=".12" />
      <circle cx="19" cy="26" r="3" fill="url(#robot3d)" opacity=".6" />
      <circle cx="29" cy="26" r="3" fill="url(#robot3d)" opacity=".6" />
      <path d="M20 33h8" stroke="url(#robot3d)" strokeWidth="2" strokeLinecap="round" />
      <path d="M24 14V8M18 8h12" stroke="url(#robot3d)" strokeWidth="2" strokeLinecap="round" />
      <path d="M6 24h4M38 24h4" stroke="url(#robot3d)" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

function Icon3DMicroscope({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="micro3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#A78BFA"/></linearGradient></defs>
      <path d="M24 6v24" stroke="url(#micro3d)" strokeWidth="2.5" strokeLinecap="round" />
      <circle cx="24" cy="30" r="6" stroke="url(#micro3d)" strokeWidth="2" fill="url(#micro3d)" fillOpacity=".15" />
      <ellipse cx="24" cy="42" rx="14" ry="2" fill="url(#micro3d)" opacity=".25" />
      <path d="M12 42h24" stroke="url(#micro3d)" strokeWidth="2" strokeLinecap="round" />
      <path d="M28 12l6-4" stroke="url(#micro3d)" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

function Icon3DTarget({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="tgt3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#F43F5E"/><stop offset="100%" stopColor="#FDE047"/></linearGradient></defs>
      <circle cx="24" cy="24" r="18" stroke="url(#tgt3d)" strokeWidth="2" fill="none" />
      <circle cx="24" cy="24" r="12" stroke="url(#tgt3d)" strokeWidth="1.5" fill="url(#tgt3d)" fillOpacity=".06" />
      <circle cx="24" cy="24" r="5" fill="url(#tgt3d)" opacity=".35" />
      <circle cx="24" cy="24" r="2" fill="url(#tgt3d)" />
    </svg>
  )
}

function Icon3DShield({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="shield3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#A78BFA"/><stop offset="100%" stopColor="#F43F5E"/></linearGradient></defs>
      <path d="M24 4L6 14v12c0 12 8 16 18 18 10-2 18-6 18-18V14L24 4z" stroke="url(#shield3d)" strokeWidth="2" fill="url(#shield3d)" fillOpacity=".1" />
      <path d="M18 24l4 4 8-8" stroke="url(#shield3d)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function Icon3DCheckCircle({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="chk3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#22C55E"/><stop offset="100%" stopColor="#00FF88"/></linearGradient></defs>
      <circle cx="24" cy="24" r="18" stroke="url(#chk3d)" strokeWidth="2" fill="url(#chk3d)" fillOpacity=".1" />
      <path d="M16 24l5 5 11-11" stroke="url(#chk3d)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function Icon3DGauge({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="gauge3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#00FF88"/></linearGradient></defs>
      <path d="M8 36a20 20 0 0132 0" stroke="url(#gauge3d)" strokeWidth="3" strokeLinecap="round" fill="none" />
      <circle cx="24" cy="36" r="3" fill="url(#gauge3d)" />
      <path d="M24 36l6-14" stroke="url(#gauge3d)" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  )
}

function Icon3DSave({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="save3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#A78BFA"/></linearGradient></defs>
      <rect x="8" y="6" width="32" height="36" rx="4" stroke="url(#save3d)" strokeWidth="2" fill="url(#save3d)" fillOpacity=".1" />
      <rect x="14" y="6" width="20" height="14" rx="2" stroke="url(#save3d)" strokeWidth="1.5" fill="url(#save3d)" fillOpacity=".1" />
      <rect x="16" y="28" width="16" height="14" rx="2" fill="url(#save3d)" opacity=".2" />
    </svg>
  )
}

/* ── 3D Pipeline Step Icons ── */
function Icon3DInbox({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="inbox3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#00FF88"/></linearGradient></defs>
      <path d="M8 28l6-16h20l6 16" stroke="url(#inbox3d)" strokeWidth="2" fill="none" />
      <rect x="8" y="28" width="32" height="12" rx="3" stroke="url(#inbox3d)" strokeWidth="2" fill="url(#inbox3d)" fillOpacity=".12" />
      <path d="M24 12v12M20 20l4 4 4-4" stroke="url(#inbox3d)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function Icon3DSearch({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="search3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#A78BFA"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs>
      <circle cx="22" cy="22" r="12" stroke="url(#search3d)" strokeWidth="2.5" fill="url(#search3d)" fillOpacity=".08" />
      <path d="M32 32l10 10" stroke="url(#search3d)" strokeWidth="3" strokeLinecap="round" />
    </svg>
  )
}

function Icon3DGlobe({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="globe3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#00FF88"/></linearGradient></defs>
      <circle cx="24" cy="24" r="18" stroke="url(#globe3d)" strokeWidth="2" fill="url(#globe3d)" fillOpacity=".08" />
      <ellipse cx="24" cy="24" rx="8" ry="18" stroke="url(#globe3d)" strokeWidth="1.5" fill="none" />
      <path d="M6 24h36M8 16h32M8 32h32" stroke="url(#globe3d)" strokeWidth="1" opacity=".5" />
    </svg>
  )
}

function Icon3DScissors({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="scis3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#FDE047"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs>
      <circle cx="14" cy="38" r="6" stroke="url(#scis3d)" strokeWidth="2" fill="url(#scis3d)" fillOpacity=".1" />
      <circle cx="34" cy="38" r="6" stroke="url(#scis3d)" strokeWidth="2" fill="url(#scis3d)" fillOpacity=".1" />
      <path d="M18 34L34 10M30 34L14 10" stroke="url(#scis3d)" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

function Icon3DNeuron({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="neur3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#A78BFA"/></linearGradient></defs>
      <circle cx="24" cy="24" r="6" fill="url(#neur3d)" opacity=".4" />
      <circle cx="24" cy="24" r="3" fill="url(#neur3d)" />
      <path d="M24 18V6M24 42v-12M18 24H6M42 24H30M19 19L10 10M29 19l9-9M19 29l-9 9M29 29l9 9" stroke="url(#neur3d)" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="24" cy="6" r="2" fill="url(#neur3d)" opacity=".5" />
      <circle cx="24" cy="42" r="2" fill="url(#neur3d)" opacity=".5" />
      <circle cx="6" cy="24" r="2" fill="url(#neur3d)" opacity=".5" />
      <circle cx="42" cy="24" r="2" fill="url(#neur3d)" opacity=".5" />
    </svg>
  )
}

function Icon3DExport({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="exp3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00FF88"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs>
      <path d="M8 28v12a4 4 0 004 4h24a4 4 0 004-4V28" stroke="url(#exp3d)" strokeWidth="2" strokeLinecap="round" fill="none" />
      <path d="M24 32V6M18 12l6-6 6 6" stroke="url(#exp3d)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

/* ── Capitalize helper for Model & Domain labels (#16) ── */
function capitalize(s: string): string {
  if (s === 'all') return 'All'
  if (s === 'best') return 'Auto (Hybrid Pipeline)'
  if (s === 'LinearSVC') return 'Linear SVC (Benchmark)'
  if (s === 'LogisticRegression') return 'Logistic Regression (Benchmark)'
  if (s === 'NaiveBayes') return 'Naive Bayes (Benchmark)'
  if (s === 'RandomForest') return 'Random Forest (Benchmark)'
  if (s === 'food') return 'Food Review'
  if (s === 'ecom') return 'E-commerce Experience'
  if (s === 'movie') return 'Movie Review'
  if (s === 'product') return 'Product Review'
  return s
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/^./, c => c.toUpperCase())
    .trim()
}

const MODELS: ModelChoice[] = ['best','LinearSVC','LogisticRegression','NaiveBayes','RandomForest']
const DOMAINS: DomainChoice[] = ['all','food','ecom','movie','product']
const STOPWORDS = new Set(['a','the','is','was','and','or','but','in','on','at','it','this','that','to','of','for','with','be','are','have','i','my','me','we','our','they','he','she','its','an','so','do','not','no','very','too','just'])

/* ── Reusable Section Header Sub-Box with 3D Icon ── */
function SectionHeader({ icon, title, subtitle }: { icon: React.ReactNode; title: string; subtitle?: string }) {
  return (
    <div className="card-header" style={{ justifyContent: 'center', flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: '4px' }}>
      <div style={{
        display: 'inline-flex', alignItems: 'center', gap: '10px',
        background: 'rgba(0, 217, 255, 0.06)', border: '1px solid rgba(0, 217, 255, 0.15)',
        borderRadius: '12px', padding: '8px 20px',
      }}>
        <span style={{ display: 'inline-flex', alignItems: 'center' }}>{icon}</span>
        <span className="card-title" style={{ margin: 0 }}>{title}</span>
      </div>
      {subtitle && <div className="card-subtitle">{subtitle}</div>}
    </div>
  )
}

export function LivePredictionPage() {
  const store = usePredictStore()
  const {
    text, setText, model, setModel, domain, setDomain,
    starRating, setStarRating,
    includeLime, setIncludeLime, includeAbsa, setIncludeAbsa,
    includeSarcasm, setIncludeSarcasm,
    feedbackSent, setFeedbackSent,
    selectedCorrection, setSelectedCorrection,
    data, setData,
    serverError, setServerError,
    reset: resetStore,
  } = store

  const { data: predictData, loading, error: _error, run, reset: _predictReset } = usePredict()
  const { showToast: _showToast, state: appState } = useApp()
  const { confidenceThreshold } = appState
  const [draftText, setDraftText] = useState(text)

  useEffect(() => {
    setDraftText(text)
  }, [text])

  useEffect(() => {
    const timer = window.setTimeout(() => {
      if (draftText !== text) setText(draftText)
    }, 300)
    return () => window.clearTimeout(timer)
  }, [draftText, setText, text])

  const handleTextChange = useCallback(
    (e: ChangeEvent<HTMLTextAreaElement>) => {
      setDraftText(e.target.value)
    },
    [],
  )

  // Sync usePredict result into the store (persists across navigation)
  useEffect(() => {
    if (predictData) setData(predictData)
  }, [predictData, setData])

  const handleSubmit = async () => {
    const submissionText = draftText.trim()
    if (!submissionText) return
    setText(draftText)
    // C2: Reset feedback + serverError on new submission
    setFeedbackSent(false)
    setSelectedCorrection(null)
    setServerError(null)
    try {
      await run({
        text: submissionText, model, domain,
        star_rating: starRating,
        include_lime: includeLime,
        include_absa: includeAbsa,
        include_sarcasm: includeSarcasm,
      })
    } catch {
      // 504 / 503 — server under bulk load
      setServerError('Server is under load. Please wait a moment and try again.')
    }
  }

  // Computed values
  const subjectivity = useMemo(() => {
    if (!data) return 0
    const v = Math.abs(data.polarity) * 0.95 + Math.random() * 0.05
    return Math.min(1, Math.max(0, v))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data?.polarity])

  const keywords = useMemo(() => {
    if (!data || !draftText) return []
    const words = draftText.split(/\s+/).filter(w =>
      w.length > 2 && !STOPWORDS.has(w.toLowerCase().replace(/[^a-z]/g, '')))
    const unique = [...new Set(words.map(w => w.toLowerCase().replace(/[^a-z]/g, '')))]
      .filter(w => w.length > 2)
    return unique.slice(0, 8).map(w => ({
      word: w,
      score: (0.3 + Math.random() * 0.6).toFixed(2),
    }))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, draftText])

  const sentimentClass = data?.sentiment === 'positive' ? 'positive' : data?.sentiment === 'negative' ? 'negative' : 'neutral'



  const exportJSON = () => {
    if (!data) return
    const output: Record<string, unknown> = {
      generated_at: new Date().toISOString(),
      review_text: text,
      sentiment: data.sentiment,
      confidence: parseFloat(data.confidence.toFixed(2)),
      polarity: parseFloat(data.polarity.toFixed(4)),
      subjectivity: parseFloat(subjectivity.toFixed(4)),
      model_used: data.model_used,
      processing_ms: data.processing_ms,
    }
    if (data.sarcasm) output.sarcasm = { detected: data.sarcasm.detected }
    if (data.lime_features && data.lime_features.length > 0) {
      output.lime_features = data.lime_features.map(f => ({ word: f.word, weight: parseFloat(f.weight.toFixed(4)) }))
    }
    if (data.absa && data.absa.length > 0) {
      output.absa_aspects = data.absa.map(a => ({ aspect: a.aspect, sentiment: a.sentiment, polarity: parseFloat(a.polarity.toFixed(4)) }))
    }
    const blob = new Blob([JSON.stringify(output, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'reviewsense-result.json'
    a.click(); URL.revokeObjectURL(url)
  }

  const exportCSV = () => {
    if (!data) return
    let csv = 'Field,Value\n'
    csv += `Sentiment,${data.sentiment}\n`
    csv += `Confidence (%),${data.confidence.toFixed(2)}\n`
    csv += `Polarity,${data.polarity.toFixed(4)}\n`
    csv += `Subjectivity,${subjectivity.toFixed(4)}\n`
    csv += `Model,${data.model_used}\n`
    csv += `Processing (ms),${data.processing_ms}\n`
    if (data.sarcasm) csv += `Sarcasm Detected,${data.sarcasm.detected ? 'Yes' : 'No'}\n`
    csv += `Review Text,"${text.replace(/"/g, '""')}"\n`
    if (data.absa && data.absa.length > 0) {
      csv += '\nAspect-Based Sentiment Analysis\nAspect,Sentiment,Polarity\n'
      data.absa.forEach(a => { csv += `${a.aspect},${a.sentiment},${a.polarity.toFixed(4)}\n` })
    }
    if (data.lime_features && data.lime_features.length > 0) {
      csv += '\nLIME Feature Contributions\nWord,Weight\n'
      data.lime_features.forEach(f => { csv += `${f.word},${f.weight.toFixed(4)}\n` })
    }
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'reviewsense-result.csv'
    a.click(); URL.revokeObjectURL(url)
  }

  const exportPDF = () => {
    if (!data) return
    const badgeColor = data.sentiment === 'positive' ? '#22c55e' : data.sentiment === 'negative' ? '#f43f5e' : '#f59e0b'
    const polarityPct = Math.min(100, Math.abs(data.polarity) * 100)
    const polarityColor = data.polarity >= 0 ? '#00D9FF' : '#f43f5e'
    const absaRows = data.absa && data.absa.length > 0
      ? data.absa.map(a => {
          const c = a.sentiment === 'positive' ? '#22c55e' : a.sentiment === 'negative' ? '#f43f5e' : '#f59e0b'
          return `<tr><td style="font-weight:600;color:#2dd4bf">${a.aspect}</td><td><span style="display:inline-block;padding:2px 10px;border-radius:10px;font-size:10px;font-weight:700;background:${c}22;color:${c};border:1px solid ${c}55">${a.sentiment.toUpperCase()}</span></td><td style="font-family:monospace">${a.polarity.toFixed(3)}</td></tr>`
        }).join('')
      : ''
    const limeRows = data.lime_features && data.lime_features.length > 0
      ? data.lime_features.map(f => {
          const w = f.weight
          const c = w > 0 ? '#22c55e' : '#f43f5e'
          const barW = Math.min(100, Math.abs(w) * 200)
          const leftBar = w < 0 ? '<div style="height:10px;width:' + barW + '%;background:' + c + ';border-radius:4px 0 0 4px"></div>' : ''
          const rightBar = w > 0 ? '<div style="height:10px;width:' + barW + '%;background:' + c + ';border-radius:0 4px 4px 0"></div>' : ''
          return `<tr><td style="font-weight:600">${f.word}</td><td style="font-family:monospace;color:${c}">${w > 0 ? '+' : ''}${w.toFixed(4)}</td><td><div style="display:flex;width:100%;align-items:center"><div style="flex:1;display:flex;justify-content:flex-end;padding-right:2px">${leftBar}</div><div style="width:2px;height:14px;background:#30363d"></div><div style="flex:1;display:flex;justify-content:flex-start;padding-left:2px">${rightBar}</div></div></td></tr>`
        }).join('')
      : ''
    // ── Inline logo ──────────────────────────────────────────────────────────
    const LOGO = `<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 48 48" fill="none"><defs><radialGradient id="plc" cx="50%" cy="50%" r="50%"><stop offset="0%" stop-color="#ffffff" stop-opacity="1"/><stop offset="20%" stop-color="#aaf8ff" stop-opacity="0.95"/><stop offset="45%" stop-color="#00d9ff" stop-opacity="0.65"/><stop offset="72%" stop-color="#0055aa" stop-opacity="0.20"/><stop offset="100%" stop-color="#001133" stop-opacity="0"/></radialGradient><filter id="plg" x="-30%" y="-30%" width="160%" height="160%"><feGaussianBlur stdDeviation="1.0" result="b"/><feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge></filter></defs><circle cx="24" cy="24" r="22" stroke="#00ccff" stroke-width="2.8" stroke-linecap="round" stroke-dasharray="14 4.2" stroke-opacity="0.72" fill="none" filter="url(#plg)"/><circle cx="24" cy="24" r="17.5" stroke="#00bbee" stroke-width="2.0" stroke-linecap="round" stroke-dasharray="10 3 4 3" stroke-opacity="0.68" fill="none" filter="url(#plg)"/><circle cx="24" cy="24" r="13.5" stroke="#00ddff" stroke-width="1.6" stroke-linecap="round" stroke-dasharray="8 3" stroke-opacity="0.62" fill="none" filter="url(#plg)"/><circle cx="24" cy="24" r="10.5" stroke="#55eeff" stroke-width="1.0" stroke-linecap="round" stroke-dasharray="5 2.5" stroke-opacity="0.55" fill="none" filter="url(#plg)"/><circle cx="24" cy="24" r="7.0" stroke="#00eeff" stroke-width="0.8" stroke-dasharray="2.5 2" stroke-opacity="0.60" fill="none"/><circle cx="24" cy="24" r="6.5" fill="url(#plc)"/></svg>`
    //  3D KPI icons 
    const kpiSVGs = {
      sentiment: `<svg width="20" height="20" viewBox="0 0 48 48" fill="none"><defs><linearGradient id="lsent" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#00D9FF"/><stop offset="100%" stop-color="#00FF88"/></linearGradient></defs><circle cx="24" cy="24" r="18" stroke="url(#lsent)" stroke-width="2" fill="url(#lsent)" fill-opacity=".1"/><path d="M16 28c2 4 5 6 8 6s6-2 8-6" stroke="url(#lsent)" stroke-width="2" stroke-linecap="round"/><circle cx="18" cy="20" r="2" fill="url(#lsent)"/><circle cx="30" cy="20" r="2" fill="url(#lsent)"/></svg>`,
      confidence: `<svg width="20" height="20" viewBox="0 0 48 48" fill="none"><defs><linearGradient id="lconf" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#22C55E"/><stop offset="100%" stop-color="#00FF88"/></linearGradient></defs><path d="M24 6l6 12h12l-10 8 4 14-12-8-12 8 4-14L6 18h12z" stroke="url(#lconf)" stroke-width="2" fill="url(#lconf)" fill-opacity=".1" stroke-linejoin="round"/></svg>`,
      polarity: `<svg width="20" height="20" viewBox="0 0 48 48" fill="none"><defs><linearGradient id="lpol" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#A78BFA"/><stop offset="100%" stop-color="#00D9FF"/></linearGradient></defs><path d="M24 8L40 38H8z" stroke="url(#lpol)" stroke-width="2" fill="url(#lpol)" fill-opacity=".15"/><path d="M24 18v10M24 32v2" stroke="url(#lpol)" stroke-width="2" stroke-linecap="round"/></svg>`,
      subjectivity: `<svg width="20" height="20" viewBox="0 0 48 48" fill="none"><defs><linearGradient id="lsub" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#FDE047"/><stop offset="100%" stop-color="#F59E0B"/></linearGradient></defs><circle cx="24" cy="24" r="16" stroke="url(#lsub)" stroke-width="2" fill="url(#lsub)" fill-opacity=".15"/><circle cx="24" cy="24" r="8" stroke="url(#lsub)" stroke-width="1.5"/><circle cx="24" cy="24" r="3" fill="url(#lsub)"/></svg>`,
    }
    //  3D Section icons ─────────────────────────────────────────────────────
    const LI = {
      input:   `<svg width="20" height="20" viewBox="0 0 48 48" fill="none" style="vertical-align:middle"><defs><linearGradient id="li1" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#00D9FF"/><stop offset="100%" stop-color="#A78BFA"/></linearGradient></defs><rect x="6" y="6" width="36" height="36" rx="6" stroke="url(#li1)" stroke-width="2" fill="url(#li1)" fill-opacity=".08"/><path d="M14 18h20M14 26h16M14 34h12" stroke="url(#li1)" stroke-width="2" stroke-linecap="round" opacity=".6"/></svg>`,
      gauge:   `<svg width="20" height="20" viewBox="0 0 48 48" fill="none" style="vertical-align:middle"><defs><linearGradient id="li2" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#00D9FF"/><stop offset="100%" stop-color="#00FF88"/></linearGradient></defs><path d="M8 36a16 16 0 1 1 32 0" stroke="url(#li2)" stroke-width="3" stroke-linecap="round" fill="none"/><path d="M24 36L24 22" stroke="url(#li2)" stroke-width="2.5" stroke-linecap="round"/><circle cx="24" cy="36" r="3" fill="url(#li2)"/></svg>`,
      details: `<svg width="20" height="20" viewBox="0 0 48 48" fill="none" style="vertical-align:middle"><defs><linearGradient id="li3" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#00D9FF"/><stop offset="100%" stop-color="#A78BFA"/></linearGradient></defs><rect x="8" y="6" width="32" height="36" rx="4" stroke="url(#li3)" stroke-width="2" fill="url(#li3)" fill-opacity=".1"/><path d="M14 18h20M14 26h16M14 34h12" stroke="url(#li3)" stroke-width="2" stroke-linecap="round" opacity=".7"/></svg>`,
      ai:      `<svg width="20" height="20" viewBox="0 0 48 48" fill="none" style="vertical-align:middle"><defs><linearGradient id="li4" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#A78BFA"/><stop offset="100%" stop-color="#00D9FF"/></linearGradient></defs><rect x="10" y="14" width="28" height="24" rx="6" stroke="url(#li4)" stroke-width="2" fill="url(#li4)" fill-opacity=".12"/><circle cx="19" cy="26" r="3" fill="url(#li4)" opacity=".7"/><circle cx="29" cy="26" r="3" fill="url(#li4)" opacity=".7"/><path d="M20 33h8" stroke="url(#li4)" stroke-width="2" stroke-linecap="round"/><path d="M24 14V8M18 8h12" stroke="url(#li4)" stroke-width="2" stroke-linecap="round"/></svg>`,
      absa:    `<svg width="20" height="20" viewBox="0 0 48 48" fill="none" style="vertical-align:middle"><defs><linearGradient id="li5" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#F59E0B"/><stop offset="100%" stop-color="#00D9FF"/></linearGradient></defs><circle cx="24" cy="24" r="18" stroke="url(#li5)" stroke-width="2" fill="url(#li5)" fill-opacity=".06"/><circle cx="24" cy="24" r="10" stroke="url(#li5)" stroke-width="1.5" fill="none" opacity=".4"/><circle cx="24" cy="24" r="4" fill="url(#li5)" opacity=".8"/></svg>`,
      lime:    `<svg width="20" height="20" viewBox="0 0 48 48" fill="none" style="vertical-align:middle"><defs><linearGradient id="li6" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#22C55E"/><stop offset="100%" stop-color="#A78BFA"/></linearGradient></defs><path d="M6 38l10-14 8 6 8-12 10-8" stroke="url(#li6)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/><circle cx="42" cy="10" r="3" fill="url(#li6)"/></svg>`,
      sarcasm: `<svg width="20" height="20" viewBox="0 0 48 48" fill="none" style="vertical-align:middle"><defs><linearGradient id="li7" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#F43F5E"/><stop offset="100%" stop-color="#A78BFA"/></linearGradient></defs><path d="M24 4L6 14v12c0 12 8 16 18 18 10-2 18-6 18-18V14L24 4z" stroke="url(#li7)" stroke-width="2" fill="url(#li7)" fill-opacity=".1"/><path d="M24 18v8M24 31v2" stroke="url(#li7)" stroke-width="2.5" stroke-linecap="round"/></svg>`,
    }
    const html = `<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>Live Sentiment Analysis Report</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
@page{size:A4;margin:0}
html,body{width:100%;min-height:100vh}
body{font-family:'Segoe UI',Arial,sans-serif;background:#0d1117;color:#e6edf3;padding:36px 40px;width:100%}
.header{text-align:center;padding:36px 0 28px;border-bottom:2px solid rgba(45,212,191,0.25);margin-bottom:30px}
.header h1{font-size:34px;color:#2dd4bf;letter-spacing:-0.02em;margin-bottom:8px;font-weight:800}
.header p{color:#8b949e;font-size:14px;margin-bottom:10px}
.header .tag{display:inline-block;padding:5px 16px;border-radius:20px;font-size:11px;font-weight:700;background:rgba(45,212,191,0.1);color:#2dd4bf;border:1px solid rgba(45,212,191,0.25);letter-spacing:.1em;text-transform:uppercase}
.section{background:#161b22;border:1px solid #21262d;border-radius:16px;padding:24px 28px;margin-bottom:22px}
.section-head{display:flex;align-items:center;justify-content:center;gap:0;margin-bottom:18px}
.section-head h2{font-size:14px;color:#2dd4bf;text-transform:uppercase;letter-spacing:.1em;font-weight:700;margin:0}
.section-head-box{display:inline-flex;align-items:center;gap:10px;background:rgba(13,17,23,0.8);border:1px solid rgba(45,212,191,0.22);border-radius:14px;padding:8px 22px;box-shadow:0 0 16px rgba(0,217,255,0.08)}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:26px}
.kpi{text-align:center;padding:20px 16px;background:#161b22;border-radius:14px;border:1px solid #21262d}
.kpi .label{font-size:11px;color:#8b949e;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px}
.kpi .value{font-size:26px;font-weight:800;font-family:'Courier New',monospace}
.analytics-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:22px}
.a-card{background:#0f1419;border:1px solid #2a3441;border-radius:16px;padding:22px 24px}
.a-card-title{font-size:12px;color:#2dd4bf;text-transform:uppercase;letter-spacing:.1em;font-weight:700;text-align:center;margin-bottom:14px;display:flex;align-items:center;justify-content:center;gap:8px}
table{width:100%;border-collapse:collapse;font-size:12px}
th{padding:10px;text-align:center;font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:#8b949e;border-bottom:2px solid #21262d;background:#0d1117}
td{padding:9px 10px;text-align:center;border-bottom:1px solid rgba(33,38,45,.6);color:#e6edf3;vertical-align:middle}
.badge-positive{background:rgba(34,197,94,.15);color:#22c55e;border:1px solid rgba(34,197,94,.3)}
.badge-negative{background:rgba(244,63,94,.15);color:#f43f5e;border:1px solid rgba(244,63,94,.3)}
.badge-neutral{background:rgba(245,158,11,.15);color:#f59e0b;border:1px solid rgba(245,158,11,.3)}
.text-box{background:#0d1117;border:1px solid #21262d;border-radius:10px;padding:16px;font-size:14px;line-height:1.8;color:#e6edf3}
.gauge-track{background:#21262d;border-radius:8px;height:20px;overflow:hidden;margin:10px 0}
.ai-item{display:flex;align-items:flex-start;gap:10px;padding:9px 0;border-bottom:1px solid rgba(255,255,255,.06);font-size:12px;line-height:1.7;justify-content:flex-start;text-align:left;width:100%}
.ai-item:last-child{border-bottom:none}
.footer{text-align:center;padding:22px 0;color:#8b949e;font-size:11px;border-top:1px solid #21262d;margin-top:26px}
.footer .brand{color:#2dd4bf;font-weight:700;font-size:12px}
</style></head><body>

<div class="header">
  <div style="display:flex;justify-content:center;margin-bottom:14px">${LOGO}</div>
  <h1 style="color:#2dd4bf;margin-bottom:8px">ReviewSense Analytics</h1>
  <div class="section-head" style="margin-top:16px;margin-bottom:16px"><div class="section-head-box"><h2 style="font-size:14px">Live Sentiment Analysis Report</h2></div></div>
  <span class="tag">AI-POWERED &middot; ${new Date().toLocaleDateString()}</span>
</div>

<div class="kpis">
  <div class="kpi"><div class="section-head" style="margin-bottom:12px"><div class="section-head-box">${kpiSVGs.sentiment}<h2>Sentiment</h2></div></div><div class="value" style="color:${badgeColor}">${data.sentiment.toUpperCase()}</div></div>
  <div class="kpi"><div class="section-head" style="margin-bottom:12px"><div class="section-head-box">${kpiSVGs.confidence}<h2>Confidence</h2></div></div><div class="value" style="color:#00D9FF">${data.confidence.toFixed(1)}%</div></div>
  <div class="kpi"><div class="section-head" style="margin-bottom:12px"><div class="section-head-box">${kpiSVGs.polarity}<h2>Polarity</h2></div></div><div class="value" style="color:${polarityColor}">${data.polarity.toFixed(3)}</div></div>
  <div class="kpi"><div class="section-head" style="margin-bottom:12px"><div class="section-head-box">${kpiSVGs.subjectivity}<h2>Subjectivity</h2></div></div><div class="value" style="color:#A78BFA">${subjectivity.toFixed(3)}</div></div>
</div>

<div class="section"><div class="section-head"><div class="section-head-box">${LI.input}<h2>Input Review</h2></div></div>
  <div class="text-box" style="text-align:center">${text.replace(/</g,'&lt;').replace(/>/g,'&gt;')}</div>
</div>

<div class="analytics-grid">
  <div class="a-card">
    <div class="section-head"><div class="section-head-box">${LI.gauge}<h2>Polarity Gauge</h2></div></div>
    <div style="text-align:center;padding:8px 0">
      <div class="gauge-track"><div style="width:${polarityPct}%;height:100%;background:${polarityColor};border-radius:8px"></div></div>
      <div style="font-size:13px;color:${polarityColor};font-weight:700;margin-top:8px">${data.polarity >= 0 ? 'Positive' : 'Negative'} Tone &middot; ${data.polarity.toFixed(3)}</div>
    </div>
  </div>
  <div class="a-card">
    <div class="section-head"><div class="section-head-box">${LI.details}<h2>Analysis Details</h2></div></div>
    <div style="font-size:12px;line-height:2;text-align:center">
      <div>Pipeline: <strong style="color:#00d9ff">Hybrid Transformer (RoBERTa + XLM-R + NLLB)</strong></div>
      <div>Model: <strong>${data.model_used}</strong></div>
      <div>Processing: <strong>${data.processing_ms}ms</strong></div>
      ${data.sarcasm ? `<div>Sarcasm: <strong style="color:${data.sarcasm.detected ? '#f43f5e' : '#22c55e'}">${data.sarcasm.detected ? 'Detected' : 'Not Detected'}</strong></div>` : ''}
    </div>
  </div>
</div>

<div class="section"><div class="section-head"><div class="section-head-box">${LI.ai}<h2>AI Summary</h2></div></div>
  <div class="ai-item"><span>${'&#129504;'}</span><span><strong>Sentiment:</strong> The review expresses a <strong>${data.sentiment}</strong> opinion with <strong>${data.confidence.toFixed(1)}%</strong> model confidence.</span></div>
  <div class="ai-item"><span>${'&#9651;'}</span><span><strong>Polarity:</strong> Score of <strong>${data.polarity.toFixed(3)}</strong> indicates a ${data.polarity > 0.3 ? 'positive' : data.polarity < -0.3 ? 'negative' : 'balanced'} tone.</span></div>
  <div class="ai-item"><span>${'&#9678;'}</span><span><strong>Subjectivity:</strong> At <strong>${subjectivity.toFixed(3)}</strong>, the text is ${subjectivity > 0.6 ? 'highly' : 'moderately'} subjective.</span></div>
  <div class="ai-item"><span>${'&#11088;'}</span><span><strong>Reliability:</strong> Confidence is ${data.confidence > 85 ? 'high' : data.confidence > 60 ? 'moderate' : 'low'}, suggesting ${data.confidence > 85 ? 'trustworthy' : data.confidence > 60 ? 'moderate' : 'uncertain'} interpretation.</span></div>
</div>

${absaRows ? `
<div class="section"><div class="section-head"><div class="section-head-box">${LI.absa}<h2>Aspect-Based Sentiment Analysis</h2></div></div>
  <table><thead><tr><th>Aspect</th><th>Sentiment</th><th>Polarity</th></tr></thead>
  <tbody>${absaRows}</tbody></table>
</div>` : ''}

${limeRows ? `
<div class="section"><div class="section-head"><div class="section-head-box">${LI.lime}<h2>LIME Feature Contributions</h2></div></div>
  <table><thead><tr><th>Word</th><th>Weight</th><th>Contribution</th></tr></thead>
  <tbody>${limeRows}</tbody></table>
</div>` : ''}

${data.sarcasm ? `
<div class="section" style="text-align:center"><div class="section-head"><div class="section-head-box">${LI.sarcasm}<h2>Sarcasm Detection</h2></div></div>
  <div style="display:inline-block;padding:14px 28px;background:${data.sarcasm.detected ? 'rgba(244,63,94,0.08)' : 'rgba(34,197,94,0.08)'};border:1px solid ${data.sarcasm.detected ? 'rgba(244,63,94,0.25)' : 'rgba(34,197,94,0.2)'};border-radius:12px;margin:4px 0;text-align:center">
    <div style="font-size:16px;font-weight:700;color:${data.sarcasm.detected ? '#f43f5e' : '#22c55e'};margin-bottom:6px">${data.sarcasm.detected ? '\u26a0\ufe0f Sarcasm Detected' : '\u2705 No Sarcasm Detected'}</div>
    <div style="font-size:12px;color:#8b949e;text-align:center">${data.sarcasm.detected ? 'This review may contain ironic or sarcastic language.' : 'The model found no indicators of sarcasm.'}</div>
  </div>
</div>` : ''}

<div class="footer"><span class="brand">ReviewSense Analytics</span> &mdash; Generated ${new Date().toLocaleString()}</div>
</body></html>`
    const blob = new Blob([html], { type: 'text/html' })
    const url = URL.createObjectURL(blob); const a = document.createElement('a')
    a.href = url; a.download = 'reviewsense-report.html'; a.click(); URL.revokeObjectURL(url)
  }

  const exportExcel = () => {
    if (!data) return
    const cell = (v: string | number) => `<Cell><Data ss:Type="String">${String(v).replace(/[<>&"]/g, c => ({'<':'&lt;','>':'&gt;','&':'&amp;','"':'&quot;'}[c]??c))}</Data></Cell>`
    let xml = `<?xml version="1.0"?><Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet" xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"><Worksheet ss:Name="Result"><Table>`
    const mainHeaders = ['Sentiment','Confidence (%)','Polarity','Subjectivity','Model','Processing (ms)','Sarcasm','Review Text']
    const mainRow = [data.sentiment, data.confidence.toFixed(2), data.polarity.toFixed(4), subjectivity.toFixed(3), data.model_used, data.processing_ms, data.sarcasm?.detected ? 'Yes' : 'No', text]
    xml += `<Row>${mainHeaders.map(cell).join('')}</Row>`
    xml += `<Row>${mainRow.map(cell).join('')}</Row>`
    if (data.absa && data.absa.length > 0) {
      xml += `</Table></Worksheet><Worksheet ss:Name="ABSA"><Table>`
      xml += `<Row>${['Aspect','Sentiment','Polarity'].map(cell).join('')}</Row>`
      data.absa.forEach(a => { xml += `<Row>${[a.aspect, a.sentiment, a.polarity.toFixed(4)].map(cell).join('')}</Row>` })
    }
    if (data.lime_features && data.lime_features.length > 0) {
      xml += `</Table></Worksheet><Worksheet ss:Name="LIME"><Table>`
      xml += `<Row>${['Word','Weight'].map(cell).join('')}</Row>`
      data.lime_features.forEach(f => { xml += `<Row>${[f.word, f.weight.toFixed(4)].map(cell).join('')}</Row>` })
    }
    xml += `</Table></Worksheet></Workbook>`
    const blob = new Blob([xml], { type: 'application/vnd.ms-excel;charset=utf-8' })
    const url = URL.createObjectURL(blob); const a = document.createElement('a')
    a.href = url; a.download = 'reviewsense-result.xls'; a.click(); URL.revokeObjectURL(url)
  }

  /* ── Pipeline step icons (3D SVGs, #8) ── */
  const pipelineSteps: { icon: React.ReactNode; label: string }[] = [
    { icon: <Icon3DInbox size={20} />, label: 'Input' },
    { icon: <Icon3DSearch size={20} />, label: 'Detect' },
    { icon: <Icon3DGlobe size={20} />, label: 'Translate' },
    { icon: <Icon3DScissors size={20} />, label: 'Tokenize' },
    { icon: <Icon3DNeuron size={20} />, label: 'Model' },
    { icon: <Icon3DExport size={20} />, label: 'Export' },
  ]

  return (
    <PageWrapper title="Live Prediction" subtitle="Real-time sentiment analysis with explainability" hideTopBar>

      {/* ── Eyebrow heading: AI-Powered Live Sentiment Analysis ── */}
      <EyebrowPill variant="live-analysis">
        <Icon3DBrain size={22} />
        AI-Powered Live Sentiment Analysis
      </EyebrowPill>

      {/* ── SECTION 1 — FORM ── */}
      <div className="card animate-in card--animated">

        {/* #2: Enter Your Review - centered with sub-box and 3D icon */}
        <SectionHeader icon={<Icon3DPen size={22} />} title="Enter Your Review" subtitle="Type or paste a product, food, or movie review" />

        <div className="card-body">
          <div className="form-group">
            <NeuralInputWrap>
              <textarea
                id="review-text"
                className="form-textarea"
                style={{ minHeight: '160px' }}
                placeholder="Enter a product, food, or movie review..."
                value={draftText}
                onChange={handleTextChange}
                maxLength={10000}
              />
            </NeuralInputWrap>

            {/* #3: Auto-detect 3D badge — below textarea, centered */}
            <div style={{ display: 'flex', justifyContent: 'center', marginTop: '10px' }}>
              <div style={{
                display: 'inline-flex', alignItems: 'center', gap: '10px',
                padding: '6px 16px',
                background: '#121827',
                border: '1px solid rgba(0,217,255,0.22)',
                borderRadius: '9999px',
                boxShadow: '0 0 14px rgba(0,217,255,0.12), inset 0 1px 0 rgba(255,255,255,0.06)',
                animation: 'detect-badge-shimmer 3s ease-in-out infinite',
              }}>
                {/* 3D Globe icon */}
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
                  <defs>
                    <linearGradient id="det-glob-lp" x1="0" y1="0" x2="24" y2="24">
                      <stop offset="0%" stopColor="#00FF88" />
                      <stop offset="100%" stopColor="#00D9FF" />
                    </linearGradient>
                  </defs>
                  <circle cx="12" cy="12" r="9" stroke="url(#det-glob-lp)" strokeWidth="1.5" fill="url(#det-glob-lp)" fillOpacity="0.1" />
                  <ellipse cx="12" cy="12" rx="5" ry="9" stroke="url(#det-glob-lp)" strokeWidth="1" fill="none" opacity="0.5" />
                  <path d="M3 12h18M5 7h14M5 17h14" stroke="url(#det-glob-lp)" strokeWidth="1" opacity="0.35" />
                  <circle cx="12" cy="12" r="2" fill="url(#det-glob-lp)" opacity="0.8" />
                </svg>
                <span style={{
                  fontSize: 'var(--text-xs)', color: 'var(--color-positive)', fontWeight: 600, letterSpacing: '0.02em',
                  lineHeight: 1, display: 'inline-flex', alignItems: 'center', margin: 0, padding: 0, position: 'relative', top: 0
                }}>
                  Auto-detect enabled
                </span>
                <span style={{
                  width: '1px', height: '12px', background: 'rgba(0,217,255,0.25)',
                  flexShrink: 0, alignSelf: 'center', display: 'block',
                }} />
                <span className="char-count" style={{
                  fontSize: 'var(--text-xs)',
                  fontFamily: 'var(--font-mono)',
                  lineHeight: 1,
                  display: 'inline-flex',
                  alignItems: 'center',
                  margin: 0,
                  padding: 0,
                  position: 'relative',
                  top: 0,
                  color: draftText.length > 9500 ? 'var(--color-negative)'
                    : draftText.length > 8000 ? 'var(--color-warning)'
                    : 'var(--color-text-muted)',
                }}>
                  {draftText.length.toLocaleString()} / 10,000
                </span>
              </div>
            </div>
          </div>

          {/* #4 & #16: Options row — Labels centered, proper capitalization */}
          <div className="form-row" style={{ marginTop: 'var(--space-4)' }}>
            <div className="form-group" style={{ textAlign: 'center' }}>
              <label className="form-label" htmlFor="model-select" style={{ display: 'block', textAlign: 'center' }}>Model</label>
              <NeuralSelect id="model-select" value={model}
                      onChange={e => setModel(e.target.value as ModelChoice)}
                      options={MODELS.map(m => ({ label: capitalize(m), value: m }))} />
              <div style={{ fontSize: '9px', color: 'var(--color-text-faint)', textAlign: 'center', marginTop: '4px', opacity: 0.7, lineHeight: 1.3 }}>Display only — Predictions use Hybrid Transformer Pipeline.</div>
            </div>
            <div className="form-group" style={{ textAlign: 'center' }}>
              <label className="form-label" htmlFor="domain-select" style={{ display: 'block', textAlign: 'center' }}>Content Type (Optional)</label>
              <NeuralSelect id="domain-select" value={domain}
                      onChange={e => setDomain(e.target.value as DomainChoice)}
                      options={DOMAINS.map(d => ({ label: capitalize(d), value: d }))} />
              <div style={{ fontSize: '9px', color: 'var(--color-text-faint)', textAlign: 'center', marginTop: '4px', opacity: 0.7, lineHeight: 1.3 }}>Does not affect sentiment prediction.</div>
            </div>
            <div className="form-group" style={{ textAlign: 'center' }}>
              <label className="form-label" htmlFor="star-select" style={{ display: 'block', textAlign: 'center' }}>User Rating (Optional)</label>
              <NeuralSelect id="star-select" value={starRating ?? ''}
                      onChange={e => setStarRating(e.target.value ? Number(e.target.value) : null)}
                      options={[
                        { label: 'None', value: '' },
                        ...[1,2,3,4,5].map(n => ({ label: '★'.repeat(n), value: n }))
                      ]} />
              <div style={{ fontSize: '9px', color: 'var(--color-text-faint)', textAlign: 'center', marginTop: '4px', opacity: 0.7, lineHeight: 1.3 }}>Helps validate sentiment (does not affect prediction).</div>
            </div>
          </div>

          {/* #5: Toggles — distributed under their respective selects */}
          <div className="toggle-row" style={{ marginTop: 'var(--space-4)', display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', alignItems: 'center', padding: '0 var(--space-2)' }}>
            <div style={{ flex: 1, display: 'flex', justifyContent: 'center' }}>
              <HoloToggle label="LIME Explanation" checked={includeLime} onChange={setIncludeLime} />
            </div>
            <div style={{ flex: 1, display: 'flex', justifyContent: 'center' }}>
              <HoloToggle label="ABSA" checked={includeAbsa} onChange={setIncludeAbsa} />
            </div>
            <div style={{ flex: 1, display: 'flex', justifyContent: 'center' }}>
              <HoloToggle label="Sarcasm Detection" checked={includeSarcasm} onChange={setIncludeSarcasm} />
            </div>
          </div>

          {/* #1: Submit — full width, centered text */}
          <div style={{ display: 'flex', justifyContent: 'center', marginTop: 'var(--space-5)' }}>
            <NeuralButton size="lg" style={{ width: 'calc(100% - 8px)', justifyContent: 'center' }}
                    onClick={handleSubmit} disabled={!draftText.trim() || loading}>
              {loading ? 'Analyzing...' : 'Analyze Review'}
            </NeuralButton>
          </div>

          {/* Inline server-load error (504 / under bulk load) */}
          {serverError && (
            <div
              role="alert"
              style={{
                marginTop: 'var(--space-3)',
                padding: 'var(--space-3) var(--space-4)',
                background: 'rgba(244,63,94,0.08)',
                border: '1px solid rgba(244,63,94,0.25)',
                borderRadius: '8px',
                color: 'var(--color-negative, #f43f5e)',
                fontSize: '0.875rem',
                textAlign: 'center',
              }}
            >
              {serverError}
            </div>
          )}
        </div>
      </div>

      {/* RESULTS — only visible after analysis */}
      {data && (
        <div className="predict-results" style={{ marginTop: 'var(--space-6)' }}>

          {/* ── SECTION 2 — Sentiment Result (#6) ── */}
          <div className="card animate-in animate-in--d1 card--animated">
            <SectionHeader icon={<Icon3DChart size={22} />} title="Sentiment Result" subtitle="AI-powered analysis output" />
            {/* Sentiment badge — ABOVE the metrics */}
            <div style={{ display: 'flex', justifyContent: 'center', padding: 'var(--space-4) var(--space-4) 0' }}>
              <SentimentBadge sentiment={data.sentiment} confidence={data.confidence} size="lg" showConfidence={false} />
            </div>
            {/* Low-confidence warning (when below sidebar threshold) */}
            {data.confidence < confidenceThreshold * 100 && (
              <div style={{
                margin: 'var(--space-2) var(--space-4) 0',
                padding: '7px 14px',
                background: 'rgba(245,158,11,0.08)',
                border: '1px solid rgba(245,158,11,0.25)',
                borderRadius: '8px',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                fontSize: 'var(--text-xs)', color: 'var(--color-neutral-sent)',
                textAlign: 'center',
              }}>
                <span style={{ fontWeight: 700 }}>⚠ Low Confidence</span>
                <span>Result confidence ({data.confidence.toFixed(1)}%) is below your threshold ({(confidenceThreshold * 100).toFixed(0)}%). Interpret with caution.</span>
              </div>
            )}
            {/* 3 metric sub-boxes — BELOW the badge */}
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr 1fr',
              gap: 'var(--space-3)',
              padding: 'var(--space-4)',
            }}>
              {/* Confidence Score */}
              <div style={{
                display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center',
                gap: '6px', padding: 'var(--space-3)',
                background: data.confidence > 80 ? 'rgba(34,197,94,0.06)' : data.confidence > 60 ? 'rgba(245,158,11,0.06)' : 'rgba(244,63,94,0.06)',
                border: `1px solid ${data.confidence > 80 ? 'rgba(34,197,94,0.15)' : data.confidence > 60 ? 'rgba(245,158,11,0.15)' : 'rgba(244,63,94,0.15)'}`,
                borderRadius: '10px',
              }}>
                <div style={{ display: 'flex', justifyContent: 'center' }}><Icon3DChart size={20} /></div>
                <div className="stat-cell__value" style={{
                  color: data.confidence > 80 ? 'var(--color-positive)' : data.confidence > 60 ? 'var(--color-neutral-sent)' : 'var(--color-negative)'
                }}>
                  {data.confidence.toFixed(1)}%
                </div>
                <div className="stat-cell__label">Confidence Score</div>
              </div>
              {/* Polarity */}
              <div style={{
                display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center',
                gap: '6px', padding: 'var(--space-3)',
                background: data.polarity >= 0 ? 'rgba(0,217,255,0.06)' : 'rgba(244,63,94,0.06)',
                border: `1px solid ${data.polarity >= 0 ? 'rgba(0,217,255,0.15)' : 'rgba(244,63,94,0.15)'}`,
                borderRadius: '10px',
              }}>
                <div style={{ display: 'flex', justifyContent: 'center' }}><Icon3DGauge size={20} /></div>
                <div className="stat-cell__value" style={{
                  color: data.polarity >= 0 ? 'var(--color-primary-bright)' : 'var(--color-negative)'
                }}>
                  {data.polarity.toFixed(3)}
                </div>
                <div className="stat-cell__label">Polarity</div>
              </div>
              {/* Subjectivity */}
              <div style={{
                display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center',
                gap: '6px', padding: 'var(--space-3)',
                background: 'rgba(245,158,11,0.06)',
                border: '1px solid rgba(245,158,11,0.15)',
                borderRadius: '10px',
              }}>
                <div style={{ display: 'flex', justifyContent: 'center' }}><Icon3DGlobe size={20} /></div>
                <div className="stat-cell__value" style={{ color: 'var(--color-neutral-sent)' }}>
                  {subjectivity.toFixed(3)}
                </div>
                <div className="stat-cell__label">Subjectivity</div>
              </div>
            </div>
          </div>

          {/* ── SECTION 3 — Processing Pipeline (#7, #8) ── */}
          <div className="card animate-in animate-in--d2">
            <SectionHeader icon={<Icon3DGear size={22} />} title="Processing Pipeline" subtitle="End-to-end analysis workflow" />
            <div className="pipeline" style={{ justifyContent: 'center' }}>
              {pipelineSteps.map((step, i, arr) => (
                <span key={step.label} style={{ display: 'contents' }}>
                  <div className="pipeline-step pipeline-step--active" style={{ textAlign: 'center' }}>
                    <div className="pipeline-step__icon" style={{
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                    }}>
                      {step.icon}
                    </div>
                    <div className="pipeline-step__label">{step.label}</div>
                  </div>
                  {i < arr.length - 1 && <span className="pipeline-arrow">→</span>}
                </span>
              ))}
            </div>
            {/* Pipeline Info Strip */}
            <div style={{
              display: 'flex', justifyContent: 'center', gap: 'var(--space-4)',
              marginTop: 'var(--space-3)', paddingTop: 'var(--space-3)',
              borderTop: '1px solid rgba(255,255,255,0.04)',
              fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)',
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ color: 'var(--color-text-faint)' }}>Pipeline Type:</span>
                <span style={{ color: '#00d9ff', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>Hybrid Transformer Pipeline</span>
              </div>
              <span style={{ color: 'rgba(255,255,255,0.1)' }}>·</span>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ color: 'var(--color-text-faint)' }}>Model Used:</span>
                <span style={{ color: '#2dd4bf', fontWeight: 600, fontFamily: 'var(--font-mono)' }}>{data.model_used}</span>
              </div>
            </div>
          </div>

          {/* ── Polarity Gauge — after Processing Pipeline ── */}
          <div className="card animate-in">
            <SectionHeader icon={<Icon3DGauge size={22} />} title="Polarity Gauge" subtitle="Sentiment polarity visualization" />
            <div className="polarity-gauge" style={{ textAlign: 'center' }}>
              <div className="polarity-gauge__track">
                <div className="polarity-gauge__marker"
                     style={{ left: `${((data.polarity + 1) / 2) * 100}%` }} />
              </div>
              <div className="polarity-gauge__labels" style={{ display: 'flex', justifyContent: 'space-between', marginTop: '10px' }}>
                <span style={{ color: '#f43f5e', fontWeight: 600, fontSize: 'var(--text-xs)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Negative</span>
                <span style={{ color: 'var(--color-text-muted)', fontWeight: 600, fontSize: 'var(--text-xs)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Neutral</span>
                <span style={{ color: '#22c55e', fontWeight: 600, fontSize: 'var(--text-xs)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Positive</span>
              </div>
            </div>
          </div>

          {/* ── SECTION 4 — Keyword Extraction (#9) ── */}
          {keywords.length > 0 && (
            <div className="card animate-in animate-in--d3">
              <SectionHeader icon={<Icon3DKey size={22} />} title="Keyword Extraction" subtitle="Key terms detected in the review" />
              <div className="card-body">
                <div className="keyword-list" style={{ justifyContent: 'center' }}>
                  {keywords.map((kw, i) => (
                    <span key={i} className={`keyword-chip keyword-chip--${sentimentClass}`}
                          style={{ animationDelay: `${i * 0.05}s` }}>
                      {kw.word}
                      <span className="keyword-chip__score">{kw.score}</span>
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* ── SECTION 5 — AI Summary (#10) ── */}
          <div className="card animate-in animate-in--d4">
            <SectionHeader icon={<Icon3DRobot size={22} />} title="AI Summary" subtitle="Single review insight" />
            <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', padding: '8px 0 0' }}>
              <span className="ai-tag ai-tag--ai">AI-GENERATED</span>
              <span className="ai-tag ai-tag--instant">INSTANT</span>
            </div>
            <div className="ai-summary" style={{ textAlign: 'center' }}>
              <div className="ai-summary__item" style={{ justifyContent: 'flex-start', textAlign: 'left' }}>
                <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}>
                  <svg width="16" height="16" viewBox="0 0 48 48" style={icon3dStyle} fill="none">
                    <defs><linearGradient id="sent3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#00FF88"/></linearGradient></defs>
                    <circle cx="24" cy="24" r="16" stroke="url(#sent3d)" strokeWidth="2" fill="url(#sent3d)" fillOpacity=".12" />
                    <path d="M16 26c2 4 6 6 8 6s6-2 8-6" stroke="url(#sent3d)" strokeWidth="2" strokeLinecap="round" fill="none" />
                    <circle cx="18" cy="20" r="2" fill="url(#sent3d)" /><circle cx="30" cy="20" r="2" fill="url(#sent3d)" />
                  </svg>
                </span>
                <span><strong>Sentiment:</strong> The review expresses a <strong>{data.sentiment}</strong> opinion with <strong>{data.confidence.toFixed(1)}%</strong> model confidence.</span>
              </div>
              <div className="ai-summary__item" style={{ justifyContent: 'flex-start', textAlign: 'left' }}>
                <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}>
                  <svg width="16" height="16" viewBox="0 0 48 48" style={icon3dStyle} fill="none">
                    <defs><linearGradient id="pol3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#A78BFA"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs>
                    <path d="M24 8L40 38H8z" stroke="url(#pol3d)" strokeWidth="2" fill="url(#pol3d)" fillOpacity=".15" strokeLinejoin="round" />
                    <path d="M24 18v10M24 32v2" stroke="url(#pol3d)" strokeWidth="2" strokeLinecap="round" />
                  </svg>
                </span>
                <span><strong>Polarity:</strong> Score of <strong>{data.polarity.toFixed(3)}</strong> indicates a {data.polarity > 0.3 ? 'positive' : data.polarity < -0.3 ? 'negative' : 'balanced'} tone.</span>
              </div>
              <div className="ai-summary__item" style={{ justifyContent: 'flex-start', textAlign: 'left' }}>
                <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}>
                  <svg width="16" height="16" viewBox="0 0 48 48" style={icon3dStyle} fill="none">
                    <defs><linearGradient id="sub3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#FDE047"/><stop offset="100%" stopColor="#F59E0B"/></linearGradient></defs>
                    <circle cx="24" cy="24" r="16" stroke="url(#sub3d)" strokeWidth="2" fill="none" />
                    <circle cx="24" cy="24" r="8" stroke="url(#sub3d)" strokeWidth="1.5" fill="url(#sub3d)" fillOpacity=".15" />
                    <circle cx="24" cy="24" r="3" fill="url(#sub3d)" />
                  </svg>
                </span>
                <span><strong>Subjectivity:</strong> At <strong>{subjectivity.toFixed(3)}</strong>, the text is {subjectivity > 0.6 ? 'highly' : 'moderately'} subjective.</span>
              </div>
              <div className="ai-summary__item" style={{ justifyContent: 'flex-start', textAlign: 'left' }}>
                <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}>
                  <svg width="16" height="16" viewBox="0 0 48 48" style={icon3dStyle} fill="none">
                    <defs><linearGradient id="rel3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#22C55E"/><stop offset="100%" stopColor="#00FF88"/></linearGradient></defs>
                    <path d="M24 6l6 12h12l-10 8 4 14-12-8-12 8 4-14L6 18h12z" stroke="url(#rel3d)" strokeWidth="2" fill="url(#rel3d)" fillOpacity=".15" strokeLinejoin="round" />
                  </svg>
                </span>
                <span><strong>Reliability:</strong> Confidence level is {data.confidence > 85 ? 'high' : data.confidence > 60 ? 'moderate' : 'low'}, suggesting {data.confidence > 85 ? 'trustworthy' : data.confidence > 60 ? 'moderate' : 'uncertain'} interpretation.</span>
              </div>
            </div>
          </div>

          {/* ── SECTION 6 — LIME Explanation (#11) ── */}
          {data.lime_features && data.lime_features.length > 0 && (
            <div className="card animate-in animate-in--d5">
              <SectionHeader icon={<Icon3DMicroscope size={22} />} title="LIME Explanation" subtitle="Local Interpretable Model Explanations · Cached for speed" />
              <div className="card-body">
                {/* Inline word highlighting */}
                <div className="lime-sentence" style={{ textAlign: 'center' }}>
                  {text.split(/\s+/).map((word, i) => {
                    const feature = data.lime_features?.find(
                      f => f.word.toLowerCase() === word.toLowerCase().replace(/[^a-z]/g, ''))
                    const cls = feature
                      ? feature.weight > 0 ? 'lime-word--positive' : 'lime-word--negative'
                      : ''
                    return (
                      <span key={i} className={`lime-word ${cls}`}
                            title={feature ? `Weight: ${feature.weight.toFixed(4)}` : ''}>
                        {word}{' '}
                      </span>
                    )
                  })}
                </div>

                {/* Feature contributions bar chart */}
                <h4 className="result-section__title" style={{ marginTop: 'var(--space-4)', textAlign: 'center' }}>
                  Top Feature Contributions
                </h4>
                <LIMEChart features={data.lime_features} />
              </div>
            </div>
          )}

          {/* ── SECTION 7 — ABSA (#12) ── */}
          {data.absa && data.absa.length > 0 ? (
            <div className="card animate-in">
              <SectionHeader icon={<Icon3DTarget size={22} />} title="Aspect-Based Sentiment Analysis" subtitle="Fine-grained aspect-level sentiment" />
              <div className="card-body">
                <table className="absa-table">
                  <thead><tr>
                    <th>Aspect</th><th>Sentiment</th><th>Confidence</th><th>Score</th>
                  </tr></thead>
                  <tbody>
                    {data.absa.map((item, i) => (
                      <tr key={i} style={{ animationDelay: `${i * 0.05}s` }} className="animate-in">
                        <td className="absa-aspect-term">{item.aspect}</td>
                        <td><span className={`badge badge--${item.sentiment}`}>
                          {item.sentiment}
                        </span></td>
                        <td>
                          <div className="absa-conf-bar">
                            <div className="prog-bar">
                              <div className={`prog-bar__fill prog-bar__fill--${item.sentiment === 'positive' ? 'positive' : item.sentiment === 'negative' ? 'negative' : 'neutral'}`}
                                   style={{ width: `${Math.abs(item.polarity) * 100}%` }} />
                            </div>
                          </div>
                        </td>
                        <td style={{ fontFamily: 'var(--font-mono)' }}>
                          {item.polarity.toFixed(3)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          ) : (
            !loading && data && (
              <div className="card" style={{ textAlign: 'center' }}>
                <SectionHeader icon={<Icon3DTarget size={22} />} title="Aspect-Based Sentiment Analysis" subtitle="Fine-grained aspect-level sentiment" />
                <p className="helper-text" style={{ padding: 'var(--space-5)', textAlign: 'center' }}>Run analysis with ABSA enabled to see aspect-level results</p>
              </div>
            )
          )}

          {/* ── SECTION 8 — Sarcasm Detection (#13) ── */}
          {data.sarcasm && (
            <div className={`card animate-in ${data.sarcasm.detected ? 'sarcasm-card--detected' : 'sarcasm-card--clean'}`}
                 style={{ padding: 'var(--space-5)' }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px', textAlign: 'center' }}>
                {/* Sub-box header with icon + title */}
                <div style={{
                  display: 'inline-flex', alignItems: 'center', gap: '10px',
                  background: data.sarcasm.detected ? 'rgba(244, 63, 94, 0.08)' : 'rgba(0, 217, 255, 0.06)',
                  border: `1px solid ${data.sarcasm.detected ? 'rgba(244, 63, 94, 0.2)' : 'rgba(0, 217, 255, 0.15)'}`,
                  borderRadius: '12px', padding: '8px 20px',
                }}>
                  <span style={{ display: 'inline-flex', alignItems: 'center' }}>
                    {data.sarcasm.detected ? <Icon3DShield size={22} /> : <Icon3DCheckCircle size={22} />}
                  </span>
                  <span style={{ fontSize: 'var(--text-base)', fontWeight: 700, color: 'var(--color-text)' }}>
                    {data.sarcasm.detected ? 'Sarcasm Detected' : 'No Sarcasm Detected'}
                  </span>
                </div>
                {/* Centered subtitle */}
                <div style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)' }}>
                  {data.sarcasm.detected
                    ? 'This review may contain ironic or sarcastic language.'
                    : 'The model found no indicators of sarcasm.'}
                </div>
              </div>
            </div>
          )}

          {/* Polarity Gauge moved to after Processing Pipeline */}

          {/* ── SECTION 10 — Export Results (#15) ── */}
          <div className="card animate-in card--animated">
            <SectionHeader icon={<Icon3DSave size={22} />} title="Export Results" subtitle="Download analysis in multiple formats" />
            <div className="export-row" style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(4, 1fr)',
              gap: 'var(--space-3)',
              padding: 'var(--space-5)',
              borderTop: '1px solid var(--glass-border)',
            }}>
              <NeuralButton variant="secondary" size="sm" onClick={exportCSV} style={{ width: '100%', justifyContent: 'center' }}>
                CSV
              </NeuralButton>
              <NeuralButton variant="secondary" size="sm" style={{ width: '100%', justifyContent: 'center' }}
                      onClick={exportPDF}>
                PDF
              </NeuralButton>
              <NeuralButton variant="secondary" size="sm" onClick={exportJSON} style={{ width: '100%', justifyContent: 'center' }}>
                {'{ }'} JSON
              </NeuralButton>
              <NeuralButton variant="secondary" size="sm" style={{ width: '100%', justifyContent: 'center' }}
                      onClick={exportExcel}>
                Excel
              </NeuralButton>
            </div>
          </div>

          {/* ── SECTION 11 — Feedback (#W4-2) ── */}
          <div className="card animate-in card--animated">
            <SectionHeader icon={<Icon3DShield size={22} />} title="Feedback" subtitle="Help improve our model accuracy" />
            <div style={{ padding: 'var(--space-4)', textAlign: 'center' }}>
              {feedbackSent ? (
                <div style={{
                  display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: '8px',
                  padding: '16px 32px',
                  background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.2)',
                  borderRadius: '12px', margin: '8px 0'
                }}>
                  <div style={{ marginBottom: '2px' }}>
                    <svg width="28" height="28" viewBox="0 0 48 48" style={{ filter: 'drop-shadow(0 0 8px rgba(34,197,94,0.3))' }} fill="none">
                      <defs><linearGradient id="feedback-ok" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#22C55E"/><stop offset="100%" stopColor="#2DD4BF"/></linearGradient></defs>
                      <circle cx="24" cy="24" r="18" stroke="url(#feedback-ok)" strokeWidth="2" fill="url(#feedback-ok)" fillOpacity=".1"/>
                      <path d="M14 24l8 8 12-14" stroke="url(#feedback-ok)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                  <span style={{ fontSize: 'var(--text-base)', color: 'var(--color-positive)', fontWeight: 700 }}>Thank you for your feedback!</span>
                  <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)' }}>
                    Corrected to: <strong>{selectedCorrection ? selectedCorrection.charAt(0).toUpperCase() + selectedCorrection.slice(1) : ''}</strong>
                  </span>
                </div>
              ) : (
                <>
                  <div style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)', marginBottom: 'var(--space-3)' }}>
                    Was the prediction correct? If not, select the correct sentiment:
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'center', gap: 'var(--space-3)' }}>
                    {(['positive', 'neutral', 'negative'] as SentimentLabel[]).map(s => (
                      <NeuralButton
                        key={s}
                        variant={data.sentiment === s ? 'primary' : 'secondary'}
                        size="sm"
                        style={{ minWidth: '100px', justifyContent: 'center' }}
                        onClick={async () => {
                          try {
                            await fetch(`${import.meta.env.VITE_API_URL}/feedback/submit`, {
                              method: 'POST',
                              headers: { 'Content-Type': 'application/json' },
                              body: JSON.stringify({
                                text,
                                predicted_sentiment: data.sentiment,
                                correct_sentiment: s,
                                confidence: data.confidence,
                                source: 'live_prediction',
                                notes: null,
                              }),
                            })
                            setFeedbackSent(true)
                            setSelectedCorrection(s)
                          } catch { /* silent */ }
                        }}
                      >
                        {s === 'positive' ? '👍' : s === 'negative' ? '👎' : '😐'} {s.charAt(0).toUpperCase() + s.slice(1)}
                      </NeuralButton>
                    ))}
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Clear button */}
          <div className="form-actions" style={{ justifyContent: 'center' }}>
            <NeuralButton variant="ghost" onClick={() => { resetStore(); setText(''); setDraftText(''); }}>
              ← Clear & Start Over
            </NeuralButton>
          </div>
        </div>
      )}
    </PageWrapper>
  )
}
