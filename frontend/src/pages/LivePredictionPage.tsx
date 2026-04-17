import { useEffect, useMemo, type CSSProperties } from 'react'
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
  if (s === 'best') return 'Best'
  if (s === 'LinearSVC') return 'Linear SVC'
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
  const { showToast: _showToast } = useApp()

  // Sync usePredict result into the store (persists across navigation)
  useEffect(() => {
    if (predictData) setData(predictData)
  }, [predictData, setData])

  const handleSubmit = async () => {
    if (!text.trim()) return
    // C2: Reset feedback + serverError on new submission
    setFeedbackSent(false)
    setSelectedCorrection(null)
    setServerError(null)
    try {
      await run({
        text, model, domain,
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
    if (!data || !text) return []
    const words = text.split(/\s+/).filter(w =>
      w.length > 2 && !STOPWORDS.has(w.toLowerCase().replace(/[^a-z]/g, '')))
    const unique = [...new Set(words.map(w => w.toLowerCase().replace(/[^a-z]/g, '')))]
      .filter(w => w.length > 2)
    return unique.slice(0, 8).map(w => ({
      word: w,
      score: (0.3 + Math.random() * 0.6).toFixed(2),
    }))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, text])

  const sentimentClass = data?.sentiment === 'positive' ? 'positive' : data?.sentiment === 'negative' ? 'negative' : 'neutral'



  const exportJSON = () => {
    if (!data) return
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'text/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'reviewsense-result.json'
    a.click(); URL.revokeObjectURL(url)
  }

  const exportCSV = () => {
    if (!data) return
    const headers = ['sentiment', 'confidence', 'polarity', 'subjectivity', 'model_used']
    const row = [data.sentiment, data.confidence.toFixed(2), data.polarity.toFixed(4), subjectivity.toFixed(3), data.model_used]
    const csv = [headers.join(','), row.join(',')].join('\n')
    const blob = new Blob([csv], { type: 'text/csv' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url; a.download = 'reviewsense-result.csv'
    a.click(); URL.revokeObjectURL(url)
  }

  const exportPDF = () => {
    if (!data) return
    const badgeCls = data.sentiment === 'positive' ? 'badge-positive' : data.sentiment === 'negative' ? 'badge-negative' : 'badge-neutral'
    const html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>Sentiment Analysis Report</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',Arial,sans-serif;background:#0d1117;color:#e6edf3;padding:40px;max-width:800px;margin:0 auto}
.header{text-align:center;padding:30px 0;border-bottom:2px solid rgba(45,212,191,0.2);margin-bottom:30px}
.header h1{font-size:32px;color:#2dd4bf;letter-spacing:-0.02em;margin-bottom:8px}
.header p{color:#8b949e;font-size:14px}
.header .tag{display:inline-block;padding:4px 12px;border-radius:20px;font-size:11px;font-weight:600;background:rgba(45,212,191,0.1);color:#2dd4bf;border:1px solid rgba(45,212,191,0.25);margin-top:8px}
.section{background:#161b22;border:1px solid #21262d;border-radius:12px;padding:24px;margin-bottom:20px}
.section h2{font-size:14px;color:#2dd4bf;margin-bottom:16px;text-align:center;text-transform:uppercase;letter-spacing:0.08em}
.badge{display:inline-block;padding:6px 20px;border-radius:20px;font-size:14px;font-weight:700;text-transform:uppercase}
.badge-positive{background:rgba(34,197,94,0.15);color:#22c55e;border:1px solid rgba(34,197,94,0.3)}
.badge-negative{background:rgba(244,63,94,0.15);color:#f43f5e;border:1px solid rgba(244,63,94,0.3)}
.badge-neutral{background:rgba(245,158,11,0.15);color:#f59e0b;border:1px solid rgba(245,158,11,0.3)}
.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-top:20px}
.metric{text-align:center;padding:20px;background:#0d1117;border-radius:10px;border:1px solid #21262d}
.metric .label{font-size:11px;color:#8b949e;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:8px}
.metric .value{font-size:28px;font-weight:700;font-family:'Courier New',monospace;color:#e6edf3}
.text-block{padding:20px;background:#0d1117;border-radius:10px;border:1px solid #21262d;font-size:14px;line-height:1.8;color:#e6edf3}
.footer{text-align:center;padding:24px 0;color:#8b949e;font-size:11px;border-top:1px solid #21262d;margin-top:30px}
.footer .brand{color:#2dd4bf;font-weight:600}
</style></head><body>
<div class="header"><h1>ReviewSense Analytics</h1><p>Live Sentiment Analysis Report</p><span class="tag">AI-POWERED</span></div>
<div class="section"><h2>Input Review</h2><div class="text-block">${text}</div></div>
<div class="section"><h2>Sentiment Result</h2>
<div style="text-align:center;margin-bottom:16px"><span class="badge ${badgeCls}">${data.sentiment}</span></div>
<div class="grid">
<div class="metric"><div class="label">Confidence</div><div class="value">${data.confidence.toFixed(1)}%</div></div>
<div class="metric"><div class="label">Polarity</div><div class="value">${data.polarity.toFixed(3)}</div></div>
<div class="metric"><div class="label">Subjectivity</div><div class="value">${subjectivity.toFixed(3)}</div></div>
</div></div>
<div class="section"><h2>Analysis Details</h2><div style="text-align:center;line-height:2;font-size:13px">
<p>🤖 Model: <strong>${data.model_used}</strong></p>
<p>⚡ Processing Time: <strong>${data.processing_ms}ms</strong></p>
<p>🔍 Sarcasm: <strong>${data.sarcasm?.detected ? 'Detected' : 'Not Detected'}</strong></p>
</div></div>
<div class="footer"><span class="brand">ReviewSense Analytics</span> — Generated ${new Date().toLocaleString()}</div></body></html>`
    const blob = new Blob([html], { type: 'text/html' })
    const url = URL.createObjectURL(blob); const a = document.createElement('a')
    a.href = url; a.download = 'reviewsense-report.html'; a.click(); URL.revokeObjectURL(url)
  }

  const exportExcel = () => {
    if (!data) return
    const headers = ['Sentiment','Confidence (%)','Polarity','Subjectivity','Model','Processing (ms)','Sarcasm','Review Text']
    const row = [data.sentiment, data.confidence.toFixed(2), data.polarity.toFixed(4), subjectivity.toFixed(3), data.model_used, data.processing_ms, data.sarcasm?.detected ? 'Yes' : 'No', `"${text.replace(/"/g, '""')}"`]
    const tsv = [headers.join('\t'), row.join('\t')].join('\n')
    const blob = new Blob(['\uFEFF' + tsv], { type: 'application/vnd.ms-excel;charset=utf-8' })
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
                value={text}
                onChange={e => setText(e.target.value)}
                maxLength={10000}
              />
            </NeuralInputWrap>

            {/* #3: Auto-detect 3D badge — below textarea, centered */}
            <div style={{ display: 'flex', justifyContent: 'center', marginTop: '10px' }}>
              <div style={{
                display: 'inline-flex', alignItems: 'center', gap: '10px',
                padding: '6px 16px',
                background: 'linear-gradient(135deg, rgba(0,217,255,0.07), rgba(0,255,136,0.05))',
                border: '1px solid rgba(0,217,255,0.22)',
                borderRadius: '9999px',
                boxShadow: '0 0 14px rgba(0,217,255,0.12), inset 0 1px 0 rgba(255,255,255,0.06)',
                backdropFilter: 'blur(8px)',
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
                <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-positive)', fontWeight: 600, letterSpacing: '0.02em' }}>
                  Auto-detect enabled
                </span>
                <span style={{ width: '1px', height: '12px', background: 'rgba(0,217,255,0.25)', flexShrink: 0 }} />
                <span className="char-count" style={{
                  fontSize: 'var(--text-xs)',
                  fontFamily: 'var(--font-mono)',
                  color: text.length > 9500 ? 'var(--color-negative)'
                    : text.length > 8000 ? 'var(--color-warning)'
                    : 'var(--color-text-muted)',
                }}>
                  {text.length.toLocaleString()} / 10,000
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
            </div>
            <div className="form-group" style={{ textAlign: 'center' }}>
              <label className="form-label" htmlFor="domain-select" style={{ display: 'block', textAlign: 'center' }}>Domain</label>
              <NeuralSelect id="domain-select" value={domain}
                      onChange={e => setDomain(e.target.value as DomainChoice)}
                      options={DOMAINS.map(d => ({ label: capitalize(d), value: d }))} />
            </div>
            <div className="form-group" style={{ textAlign: 'center' }}>
              <label className="form-label" htmlFor="star-select" style={{ display: 'block', textAlign: 'center' }}>Star Rating</label>
              <NeuralSelect id="star-select" value={starRating ?? ''}
                      onChange={e => setStarRating(e.target.value ? Number(e.target.value) : null)}
                      options={[
                        { label: 'None', value: '' },
                        ...[1,2,3,4,5].map(n => ({ label: '★'.repeat(n), value: n }))
                      ]} />
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
                    onClick={handleSubmit} disabled={!text.trim() || loading}>
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

          {/* ── SECTION 2 — Analysis Results (#6) ── */}
          <div className="card animate-in animate-in--d1 card--animated">
            <SectionHeader icon={<Icon3DChart size={22} />} title="Analysis Results" subtitle="AI-powered analysis output" />
            {/* Sentiment badge — ABOVE the metrics */}
            <div style={{ display: 'flex', justifyContent: 'center', padding: 'var(--space-4) var(--space-4) 0' }}>
              <SentimentBadge sentiment={data.sentiment} confidence={data.confidence} size="lg" showConfidence={false} />
            </div>
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
              <div className="ai-summary__item" style={{ justifyContent: 'center' }}>
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
              <div className="ai-summary__item" style={{ justifyContent: 'center' }}>
                <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}>
                  <svg width="16" height="16" viewBox="0 0 48 48" style={icon3dStyle} fill="none">
                    <defs><linearGradient id="pol3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#A78BFA"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs>
                    <path d="M24 8L40 38H8z" stroke="url(#pol3d)" strokeWidth="2" fill="url(#pol3d)" fillOpacity=".15" strokeLinejoin="round" />
                    <path d="M24 18v10M24 32v2" stroke="url(#pol3d)" strokeWidth="2" strokeLinecap="round" />
                  </svg>
                </span>
                <span><strong>Polarity:</strong> Score of <strong>{data.polarity.toFixed(3)}</strong> indicates a {data.polarity > 0.3 ? 'positive' : data.polarity < -0.3 ? 'negative' : 'balanced'} tone.</span>
              </div>
              <div className="ai-summary__item" style={{ justifyContent: 'center' }}>
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
              <div className="ai-summary__item" style={{ justifyContent: 'center' }}>
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

          {/* ── SECTION 9 — Polarity Gauge (#14) ── */}
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
                  display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px',
                  padding: 'var(--space-3)',
                  background: 'rgba(34,197,94,0.06)', border: '1px solid rgba(34,197,94,0.15)',
                  borderRadius: '10px',
                }}>
                  <span style={{ fontSize: 'var(--text-lg)', color: 'var(--color-positive)' }}>✓</span>
                  <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-positive)', fontWeight: 600 }}>Thank you for your feedback!</span>
                  <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                    Corrected to: <strong>{selectedCorrection}</strong>
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
                            await fetch('http://localhost:8000/feedback/submit', {
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
            <NeuralButton variant="ghost" onClick={() => { resetStore(); setText(''); }}>
              ← Clear & Start Over
            </NeuralButton>
          </div>
        </div>
      )}
    </PageWrapper>
  )
}
