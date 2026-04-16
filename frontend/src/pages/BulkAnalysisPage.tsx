import { useState, useCallback, useRef, useEffect, useMemo, type CSSProperties } from 'react'
import { SentimentBadge, AnalysisErrorSummary } from '@/components/ui/Badge'
import { NeuralInputWrap } from '@/components/ui/NeuralInputWrap'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { NeuralButton } from '@/components/ui/NeuralButton'
import { EyebrowPill } from '@/components/ui/EyebrowPill'
import { HoloToggle } from '@/components/ui/HoloToggle'
import { FolderUpload } from '@/components/ui/FolderUpload'
import { OrbitalLoader } from '@/components/ui/OrbitalLoader'
import { SentimentPieChart } from '@/components/charts/SentimentPieChart'
import { TopKeywordsChart } from '@/components/charts/TopKeywordsChart'
import { SentimentTrendChart } from '@/components/charts/SentimentTrendChart'
import { useBulk } from '@/hooks/useBulk'
import { useApp } from '@/context/AppContext'
import { generateUniversalPDF, generateUniversalCSV, generateUniversalExcel, generateUniversalJSON } from '@/utils/exportUtils'

type BulkStage = 'upload' | 'configure' | 'processing' | 'results'

const STOPWORDS = new Set(['a','the','is','was','and','or','but','in','on','at','it','this','that','to','of','for','with','be','are','have','i','my','me','we','they'])

/* ── 3D Icon Style ── */
const icon3dStyle: CSSProperties = {
  filter: 'drop-shadow(0 4px 8px rgba(0,217,255,0.35)) drop-shadow(0 1px 2px rgba(0,0,0,0.4))',
  transform: 'perspective(400px) rotateY(-12deg) rotateX(5deg)',
  display: 'inline-block',
  flexShrink: 0,
}

/* ── 3D Icon Components ── */
function Icon3DUpload({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="upl3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#00FF88"/></linearGradient></defs>
      <path d="M8 32v8a4 4 0 004 4h24a4 4 0 004-4v-8" stroke="url(#upl3d)" strokeWidth="2" strokeLinecap="round" fill="none" />
      <path d="M24 34V8M16 16l8-8 8 8" stroke="url(#upl3d)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function Icon3DSteps({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="stp3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#A78BFA"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs>
      <circle cx="10" cy="24" r="5" stroke="url(#stp3d)" strokeWidth="2" fill="url(#stp3d)" fillOpacity=".15" />
      <circle cx="24" cy="24" r="5" stroke="url(#stp3d)" strokeWidth="2" fill="url(#stp3d)" fillOpacity=".25" />
      <circle cx="38" cy="24" r="5" stroke="url(#stp3d)" strokeWidth="2" fill="url(#stp3d)" fillOpacity=".35" />
      <path d="M15 24h4M29 24h4" stroke="url(#stp3d)" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

function Icon3DFile({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="fil3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00FF88"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs>
      <path d="M12 6h16l12 12v24a4 4 0 01-4 4H12a4 4 0 01-4-4V10a4 4 0 014-4z" stroke="url(#fil3d)" strokeWidth="2" fill="url(#fil3d)" fillOpacity=".1" />
      <path d="M28 6v12h12" stroke="url(#fil3d)" strokeWidth="2" strokeLinecap="round" />
      <path d="M16 28h16M16 34h10" stroke="url(#fil3d)" strokeWidth="1.5" strokeLinecap="round" opacity=".5" />
    </svg>
  )
}

function Icon3DColumns({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="col3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#FDE047"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs>
      <rect x="6" y="8" width="12" height="32" rx="3" stroke="url(#col3d)" strokeWidth="2" fill="url(#col3d)" fillOpacity=".1" />
      <rect x="22" y="8" width="12" height="32" rx="3" stroke="url(#col3d)" strokeWidth="2" fill="url(#col3d)" fillOpacity=".2" />
      <rect x="38" y="8" width="4" height="32" rx="2" fill="url(#col3d)" opacity=".15" />
    </svg>
  )
}

function Icon3DGearSettings({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="gs3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#A78BFA"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs>
      <path d="M24 16a8 8 0 100 16 8 8 0 000-16z" stroke="url(#gs3d)" strokeWidth="2" fill="url(#gs3d)" fillOpacity=".15" />
      <path d="M24 4v6M24 38v6M4 24h6M38 24h6M9.9 9.9l4.2 4.2M33.9 33.9l4.2 4.2M38.1 9.9l-4.2 4.2M14.1 33.9l-4.2 4.2" stroke="url(#gs3d)" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  )
}



function Icon3DResults({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="res3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#A78BFA"/></linearGradient></defs>
      <rect x="6" y="6" width="36" height="36" rx="6" stroke="url(#res3d)" strokeWidth="2" fill="url(#res3d)" fillOpacity=".08" />
      <path d="M14 18h20M14 26h16M14 34h12" stroke="url(#res3d)" strokeWidth="2" strokeLinecap="round" opacity=".6" />
    </svg>
  )
}

function Icon3DPie({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="pie3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#22C55E"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs>
      <circle cx="24" cy="24" r="18" stroke="url(#pie3d)" strokeWidth="2" fill="url(#pie3d)" fillOpacity=".08" />
      <path d="M24 6v18h18" stroke="url(#pie3d)" strokeWidth="2" strokeLinecap="round" />
      <path d="M24 24L12 38" stroke="url(#pie3d)" strokeWidth="1.5" strokeLinecap="round" opacity=".5" />
    </svg>
  )
}

function Icon3DKeyword({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="kw3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#FDE047"/><stop offset="100%" stopColor="#F59E0B"/></linearGradient></defs>
      <circle cx="16" cy="20" r="10" stroke="url(#kw3d)" strokeWidth="2" fill="url(#kw3d)" fillOpacity=".12" />
      <path d="M24 24h18M36 24v8M42 24v6" stroke="url(#kw3d)" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  )
}

function Icon3DTrend({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="trd3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#00FF88"/></linearGradient></defs>
      <path d="M6 38l10-14 8 6 8-12 10-8" stroke="url(#trd3d)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
      <circle cx="42" cy="10" r="3" fill="url(#trd3d)" />
    </svg>
  )
}

function Icon3DRobot({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="brb3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#00FF88"/></linearGradient></defs>
      <rect x="10" y="14" width="28" height="24" rx="6" stroke="url(#brb3d)" strokeWidth="2" fill="url(#brb3d)" fillOpacity=".12" />
      <circle cx="19" cy="26" r="3" fill="url(#brb3d)" opacity=".6" />
      <circle cx="29" cy="26" r="3" fill="url(#brb3d)" opacity=".6" />
      <path d="M20 33h8" stroke="url(#brb3d)" strokeWidth="2" strokeLinecap="round" />
      <path d="M24 14V8M18 8h12" stroke="url(#brb3d)" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

function Icon3DSave({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="bsv3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#A78BFA"/></linearGradient></defs>
      <rect x="8" y="6" width="32" height="36" rx="4" stroke="url(#bsv3d)" strokeWidth="2" fill="url(#bsv3d)" fillOpacity=".1" />
      <rect x="14" y="6" width="20" height="14" rx="2" stroke="url(#bsv3d)" strokeWidth="1.5" fill="url(#bsv3d)" fillOpacity=".1" />
      <rect x="16" y="28" width="16" height="14" rx="2" fill="url(#bsv3d)" opacity=".2" />
    </svg>
  )
}

function Icon3DTotal({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="tot3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#A78BFA"/></linearGradient></defs>
      <rect x="6" y="6" width="36" height="36" rx="8" stroke="url(#tot3d)" strokeWidth="2" fill="url(#tot3d)" fillOpacity=".1" />
      <path d="M17 24h14M24 17v14" stroke="url(#tot3d)" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  )
}

function Icon3DPositive({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="pos3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#22C55E"/><stop offset="100%" stopColor="#00FF88"/></linearGradient></defs>
      <circle cx="24" cy="24" r="18" stroke="url(#pos3d)" strokeWidth="2" fill="url(#pos3d)" fillOpacity=".1" />
      <path d="M16 28c2 4 5 6 8 6s6-2 8-6" stroke="url(#pos3d)" strokeWidth="2" strokeLinecap="round" fill="none" />
      <circle cx="18" cy="20" r="2" fill="url(#pos3d)" /><circle cx="30" cy="20" r="2" fill="url(#pos3d)" />
    </svg>
  )
}

function Icon3DNegative({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="neg3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#F43F5E"/><stop offset="100%" stopColor="#FB7185"/></linearGradient></defs>
      <circle cx="24" cy="24" r="18" stroke="url(#neg3d)" strokeWidth="2" fill="url(#neg3d)" fillOpacity=".1" />
      <path d="M16 32c2-4 5-6 8-6s6 2 8 6" stroke="url(#neg3d)" strokeWidth="2" strokeLinecap="round" fill="none" />
      <circle cx="18" cy="20" r="2" fill="url(#neg3d)" /><circle cx="30" cy="20" r="2" fill="url(#neg3d)" />
    </svg>
  )
}

function Icon3DNeutral({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="neu3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#FDE047"/><stop offset="100%" stopColor="#F59E0B"/></linearGradient></defs>
      <circle cx="24" cy="24" r="18" stroke="url(#neu3d)" strokeWidth="2" fill="url(#neu3d)" fillOpacity=".1" />
      <path d="M16 30h16" stroke="url(#neu3d)" strokeWidth="2" strokeLinecap="round" />
      <circle cx="18" cy="20" r="2" fill="url(#neu3d)" /><circle cx="30" cy="20" r="2" fill="url(#neu3d)" />
    </svg>
  )
}

function Icon3DSarcasm({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="sar3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#A78BFA"/><stop offset="100%" stopColor="#F43F5E"/></linearGradient></defs>
      <path d="M24 4L6 14v12c0 12 8 16 18 18 10-2 18-6 18-18V14L24 4z" stroke="url(#sar3d)" strokeWidth="2" fill="url(#sar3d)" fillOpacity=".1" />
      <path d="M24 18v8M24 30v2" stroke="url(#sar3d)" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  )
}

/* ── Reusable Section Sub-Box Header ── */
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
      {subtitle && <div className="card-subtitle" style={{ textAlign: 'center' }}>{subtitle}</div>}
    </div>
  )
}

/* ── Capitalize helper ── */
function formatModelName(s: string): string {
  if (s === 'best') return 'Best'
  return s
    .replace(/([A-Z])/g, ' $1')
    .replace(/^./, c => c.toUpperCase())
    .trim()
}

/* ── 3D Bulk/Stack icon for eyebrow (unique to this page) ── */
function Icon3DBulkStack({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" style={icon3dStyle} fill="none">
      <defs>
        <linearGradient id="bstk3d" x1="0" y1="0" x2="64" y2="64">
          <stop offset="0%" stopColor="#A78BFA" />
          <stop offset="100%" stopColor="#00D9FF" />
        </linearGradient>
      </defs>
      <rect x="10" y="32" width="44" height="10" rx="4" stroke="url(#bstk3d)" strokeWidth="2" fill="url(#bstk3d)" fillOpacity=".25" />
      <rect x="14" y="22" width="36" height="10" rx="4" stroke="url(#bstk3d)" strokeWidth="2" fill="url(#bstk3d)" fillOpacity=".15" />
      <rect x="18" y="12" width="28" height="10" rx="4" stroke="url(#bstk3d)" strokeWidth="2" fill="url(#bstk3d)" fillOpacity=".08" />
      <path d="M24 50h16" stroke="url(#bstk3d)" strokeWidth="2" strokeLinecap="round" opacity=".4" />
    </svg>
  )
}

export function BulkAnalysisPage() {
  const { showToast } = useApp()
  const [stage, setStage] = useState<BulkStage>('upload')
  const [file, setFile] = useState<File | null>(null)
  const [textColumn, setTextColumn] = useState('')
  const [model, setModel] = useState('best')
  const [runAbsa, setRunAbsa] = useState(false)
  const [runSarcasm, setRunSarcasm] = useState(true)
  const [isMultilingual, setIsMultilingual] = useState(false)
  const [showAll, setShowAll] = useState(false)
  const [elapsed, setElapsed] = useState(0)
  const [logs, setLogs] = useState<string[]>([])
  const [prevLogCount, setPrevLogCount] = useState(0)
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null)

  const { jobId, result, error, columns, preview, submit, reset, previewColumns } = useBulk()
  const terminalRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (stage === 'processing') {
      setElapsed(0)
      setLogs(['Starting analysis pipeline...'])
      timerRef.current = setInterval(() => setElapsed(e => e + 1), 1000)
    } else {
      if (timerRef.current) clearInterval(timerRef.current)
    }
    return () => { if (timerRef.current) clearInterval(timerRef.current) }
  }, [stage])

  // Use real backend logs — delivered per-row via polling
  useEffect(() => {
    if (stage === 'processing' && result?.logs && result.logs.length > 0) {
      setLogs(result.logs)
    }
  }, [result?.logs, stage])

  // Auto-scroll terminal to bottom on new logs + track prevLogCount for animation
  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight
    }
    // Delay prevLogCount update so new lines get the fade-in animation first
    const timer = setTimeout(() => setPrevLogCount(logs.length), 250)
    return () => clearTimeout(timer)
  }, [logs])

  useEffect(() => {
    if (result?.status === 'completed' && stage === 'processing') setStage('results')
    if (result?.status === 'failed' && stage === 'processing') {
      // Keep showing processing view with error — don't transition
      // The error is shown inline in the processing state
    }
  }, [result?.status, stage])

  const handleFileSelect = useCallback(async (f: File) => {
    setFile(f)
    const cols = await previewColumns(f)
    if (cols.length > 0) { setTextColumn(cols[0]); setStage('configure') }
  }, [previewColumns])

  const handleSubmit = useCallback(async () => {
    if (!file) return
    setStage('processing')
    await submit(file, textColumn, model, runAbsa, runSarcasm, isMultilingual)
  }, [file, textColumn, model, runAbsa, runSarcasm, isMultilingual, submit])

  const handleReset = useCallback(() => {
    reset(); setFile(null); setStage('upload'); setShowAll(false); setLogs([])
  }, [reset])

  // Compute keywords from results
  const topKeywords = useMemo(() => {
    if (!result?.results) return []
    const wordCounts: Record<string, { positive: number; negative: number }> = {}
    result.results.forEach(r => {
      r.text.split(/\s+/).forEach(w => {
        const clean = w.toLowerCase().replace(/[^a-z]/g, '')
        if (clean.length > 3 && !STOPWORDS.has(clean)) {
          if (!wordCounts[clean]) wordCounts[clean] = { positive: 0, negative: 0 }
          if (r.sentiment === 'positive') wordCounts[clean].positive++
          else if (r.sentiment === 'negative') wordCounts[clean].negative++
        }
      })
    })
    return Object.entries(wordCounts)
      .map(([word, counts]) => ({ word, ...counts }))
      .sort((a, b) => (b.positive + b.negative) - (a.positive + a.negative))
      .slice(0, 10)
  }, [result?.results])

  // Compute trend from results batches
  const trendData = useMemo(() => {
    if (!result?.results || result.results.length < 5) return undefined
    const batchSize = Math.max(1, Math.floor(result.results.length / 6))
    const batches = []
    for (let i = 0; i < result.results.length; i += batchSize) {
      const batch = result.results.slice(i, i + batchSize)
      const total = batch.length || 1
      batches.push({
        month: `Batch ${batches.length + 1}`,
        positive: Math.round(batch.filter(r => r.sentiment === 'positive').length / total * 100),
        negative: Math.round(batch.filter(r => r.sentiment === 'negative').length / total * 100),
        neutral: Math.round(batch.filter(r => r.sentiment === 'neutral').length / total * 100),
      })
    }
    return batches.slice(0, 6)
  }, [result?.results])

  const exportCSV = useCallback(() => {
    if (!result?.results || result.results.length === 0) { showToast('error', 'No results to export'); return }
    generateUniversalCSV({ rows: result.results, mode: 'bulk', filename: `reviewsense-bulk-${jobId ?? 'export'}.csv` })
    showToast('success', 'CSV exported successfully')
  }, [result, jobId, showToast])

  const exportPDF = useCallback(() => {
    if (!result?.results || !result.summary) { showToast('error', 'No results to export'); return }
    generateUniversalPDF({
      title: 'ReviewSense Analytics',
      subtitle: `Bulk Sentiment Analysis Report — ${result.summary.total_analyzed} Reviews`,
      rows: result.results,
      summary: result.summary,
      mode: 'bulk',
      topKeywords,
      trendBatches: trendData,
      filename: `reviewsense-bulk-${jobId ?? 'report'}.html`,
    })
    showToast('success', 'PDF report downloaded')
  }, [result, jobId, topKeywords, trendData, showToast])

  const exportExcel = useCallback(() => {
    if (!result?.results || result.results.length === 0) { showToast('error', 'No results to export'); return }
    generateUniversalExcel({ rows: result.results, mode: 'bulk', filename: `reviewsense-bulk-${jobId ?? 'export'}.xls` })
    showToast('success', 'Excel file downloaded')
  }, [result, jobId, showToast])

  const displayRows = result?.results
    ? (showAll ? result.results : result.results.slice(0, 10))
    : []

  return (
    <PageWrapper title="Bulk Analysis" subtitle="Upload a CSV and analyze thousands of reviews" hideTopBar>

      {/* ── Eyebrow heading ── */}
      <EyebrowPill variant="bulk-dashboard">
        <Icon3DBulkStack size={22} />
        Bulk Sentiment Analysis Dashboard
      </EyebrowPill>

      {/* STATE 1: UPLOAD */}
      {stage === 'upload' && (
        <>
          {/* Upload Instructions */}
          <div className="card animate-in card--animated">
            <SectionHeader icon={<Icon3DUpload size={22} />} title="Upload Instructions" subtitle="Supported file formats and guidelines" />
            <div className="card-body" style={{ textAlign: 'center' }}>
              <p className="helper-text" style={{ textAlign: 'center' }}>
                Upload a CSV file containing reviews. Configure analysis settings, then let our ML pipeline
                process every review with sentiment classification, sarcasm detection, and more.
              </p>
            </div>
          </div>

          {/* How It Works */}
          <div className="card animate-in animate-in--d1" style={{ marginTop: 'var(--space-4)' }}>
            <SectionHeader icon={<Icon3DSteps size={22} />} title="How It Works" subtitle="Simple three-step analysis workflow" />
            <div style={{
              display: 'grid',
              gridTemplateColumns: '1fr 1fr 1fr',
              gap: 'var(--space-4)',
              padding: 'var(--space-5)',
            }}>
              {/* Step 1 */}
              <div style={{
                display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center',
                gap: 'var(--space-3)', padding: 'var(--space-4)',
                background: 'rgba(0,217,255,0.04)', border: '1px solid rgba(0,217,255,0.12)',
                borderRadius: '12px',
              }}>
                <div style={{ display: 'flex', justifyContent: 'center' }}><Icon3DUpload size={32} /></div>
                <div style={{
                  display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                  width: '28px', height: '28px', borderRadius: '50%',
                  background: 'rgba(0,217,255,0.15)', border: '1px solid rgba(0,217,255,0.3)',
                  fontSize: 'var(--text-xs)', fontWeight: 700, color: 'var(--color-primary-bright)',
                  fontFamily: 'var(--font-mono)',
                }}>01</div>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 'var(--text-sm)', color: 'var(--color-text)', marginBottom: '4px' }}>Upload CSV</div>
                  <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', lineHeight: 1.5 }}>Drag &amp; drop or browse for your review file</div>
                </div>
              </div>
              {/* Step 2 */}
              <div style={{
                display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center',
                gap: 'var(--space-3)', padding: 'var(--space-4)',
                background: 'rgba(167,139,250,0.04)', border: '1px solid rgba(167,139,250,0.12)',
                borderRadius: '12px',
              }}>
                <div style={{ display: 'flex', justifyContent: 'center' }}><Icon3DColumns size={32} /></div>
                <div style={{
                  display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                  width: '28px', height: '28px', borderRadius: '50%',
                  background: 'rgba(167,139,250,0.15)', border: '1px solid rgba(167,139,250,0.3)',
                  fontSize: 'var(--text-xs)', fontWeight: 700, color: '#a78bfa',
                  fontFamily: 'var(--font-mono)',
                }}>02</div>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 'var(--text-sm)', color: 'var(--color-text)', marginBottom: '4px' }}>Configure Columns</div>
                  <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', lineHeight: 1.5 }}>Select the text column and analysis model</div>
                </div>
              </div>
              {/* Step 3 */}
              <div style={{
                display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center',
                gap: 'var(--space-3)', padding: 'var(--space-4)',
                background: 'rgba(0,255,136,0.04)', border: '1px solid rgba(0,255,136,0.12)',
                borderRadius: '12px',
              }}>
                <div style={{ display: 'flex', justifyContent: 'center' }}><Icon3DResults size={32} /></div>
                <div style={{
                  display: 'inline-flex', alignItems: 'center', justifyContent: 'center',
                  width: '28px', height: '28px', borderRadius: '50%',
                  background: 'rgba(0,255,136,0.15)', border: '1px solid rgba(0,255,136,0.3)',
                  fontSize: 'var(--text-xs)', fontWeight: 700, color: '#00ff88',
                  fontFamily: 'var(--font-mono)',
                }}>03</div>
                <div>
                  <div style={{ fontWeight: 700, fontSize: 'var(--text-sm)', color: 'var(--color-text)', marginBottom: '4px' }}>Analyze &amp; Export</div>
                  <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', lineHeight: 1.5 }}>View results and download reports</div>
                </div>
              </div>
            </div>
          </div>

          {/* Drag & Drop */}
          <div className="card animate-in animate-in--d2 card--animated" style={{ marginTop: 'var(--space-4)', textAlign: 'center' }}>
            <FolderUpload onFileSelect={handleFileSelect} />
          </div>
        </>
      )}

      {/* STATE 2: CONFIGURE */}
      {stage === 'configure' && file && (
        <>
          {/* File Uploaded */}
          <div className="card animate-in card--animated">
            <SectionHeader icon={<Icon3DFile size={22} />} title="File Uploaded" subtitle="Review your uploaded dataset" />
            <div className="card-body" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '8px', textAlign: 'center' }}>
              <div>
                <div style={{ fontWeight: 600 }}>{file.name}</div>
                <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', marginTop: 2 }}>
                  {(file.size / 1024).toFixed(0)} KB · {columns.length} columns detected · Ready
                </div>
              </div>
              <NeuralButton variant="ghost" size="sm"
                      onClick={() => { setFile(null); setStage('upload') }}>
                Change File
              </NeuralButton>
            </div>
          </div>

          {/* Column Mapping */}
          <div className="card animate-in animate-in--d1 card--animated" style={{ marginTop: 'var(--space-4)' }}>
            <SectionHeader icon={<Icon3DColumns size={22} />} title="Column Mapping" subtitle="Select the text column for analysis" />
            <div className="card-body">
              <div className="form-group" style={{ textAlign: 'center' }}>
                <label className="form-label" htmlFor="text-col" style={{ textAlign: 'center', display: 'block' }}>Text Column</label>
                <NeuralInputWrap>
                  <select id="text-col" className="form-select" value={textColumn}
                          onChange={e => setTextColumn(e.target.value)}>
                    {columns.map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </NeuralInputWrap>
              </div>
              {preview.length > 0 && (
                <div className="preview-table-wrap" style={{ marginTop: 'var(--space-4)' }}>
                  <table className="preview-table">
                    <thead><tr><th style={{ textAlign: 'center' }}>Row</th><th style={{ textAlign: 'center' }}>{textColumn}</th></tr></thead>
                    <tbody>
                      {preview.slice(0, 5).map((row, i) => (
                        <tr key={i}><td style={{ textAlign: 'center' }}>{i + 1}</td><td style={{ textAlign: 'center' }}>{String(row[textColumn] ?? '').slice(0, 100)}</td></tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>

          {/* Analysis Settings */}
          <div className="card animate-in animate-in--d2" style={{ marginTop: 'var(--space-4)' }}>
            <SectionHeader icon={<Icon3DGearSettings size={22} />} title="Analysis Settings" subtitle="Configure model and detection options" />
            <div className="card-body">
              <div className="form-row" style={{ justifyContent: 'center' }}>
                <div className="form-group" style={{ textAlign: 'center' }}>
                  <label className="form-label" htmlFor="bulk-model" style={{ textAlign: 'center', display: 'block' }}>Model</label>
                  <NeuralInputWrap>
                    <select id="bulk-model" className="form-select" value={model}
                            onChange={e => setModel(e.target.value)}>
                      {['best','LinearSVC','LogisticRegression','NaiveBayes','RandomForest'].map(m =>
                        <option key={m} value={m}>{formatModelName(m)}</option>)}
                    </select>
                  </NeuralInputWrap>
                </div>
              </div>
              {/*
                Toggle row: .analysis-toggle-grid — CSS grid repeat(3,1fr)
                Verified stable: 1280px / 1024px / 768px (3-column)
                Mobile ≤640px: stacks vertically (1-column) via @media rule
                in animations.css. Phase 9 audit: 2026-04-16 — Item 4.
              */}
              <div className="analysis-toggle-grid">
                <div style={{ display: 'flex', justifyContent: 'flex-start' }}>
                  <HoloToggle label="ABSA (Slower)" checked={runAbsa} onChange={setRunAbsa} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'center' }}>
                  <HoloToggle label="Enable Multilingual Analysis" checked={isMultilingual} onChange={setIsMultilingual} />
                </div>
                <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
                  <HoloToggle label="Sarcasm Detection" checked={runSarcasm} onChange={setRunSarcasm} />
                </div>
              </div>
            </div>
          </div>

          <div style={{ display: 'flex', justifyContent: 'center', marginTop: 'var(--space-4)' }}>
            <NeuralButton size="lg" style={{ width: '80%', maxWidth: '500px', justifyContent: 'center' }}
                    onClick={handleSubmit}>
              Analyze All Reviews
            </NeuralButton>
          </div>
        </>
      )}

      {/* STATE 3: PROCESSING — Single unified loading */}
      {stage === 'processing' && (
        <div className="card animate-in" style={{ padding: 'var(--space-4)' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--space-3)' }}>
            {/* Chip loader animation */}
            <OrbitalLoader text="" />

            {/* Status sub-box */}
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: '10px',
              background: 'rgba(0, 217, 255, 0.06)', border: '1px solid rgba(0, 217, 255, 0.15)',
              borderRadius: '12px', padding: '8px 20px', textAlign: 'center',
            }}>
              <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-primary-bright)', fontWeight: 600 }}>
                {result?.status === 'failed' ? 'Analysis Failed' : 'Analyzing Reviews'}
              </span>
              <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>
                {result?.processed ?? 0}/{result?.total_rows ?? '?'} · {Math.floor(elapsed / 60)}m {elapsed % 60}s
              </span>
            </div>

            {/* Terminal logs sub-box */}
            <div style={{
              width: '100%', maxWidth: '520px',
              background: 'rgba(0, 0, 0, 0.4)', border: '1px solid rgba(0, 217, 255, 0.1)',
              borderRadius: '10px', overflow: 'hidden',
            }}>
              {/* Terminal header */}
              <div style={{
                display: 'flex', alignItems: 'center', gap: '6px',
                padding: '8px 14px', borderBottom: '1px solid rgba(255,255,255,0.06)',
                background: 'rgba(0,0,0,0.3)',
              }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ff5f57' }} />
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ffbd2e' }} />
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#28ca41' }} />
                <span style={{ flex: 1, textAlign: 'center', fontSize: '10px', color: 'var(--color-text-faint)', fontFamily: 'var(--font-mono)', letterSpacing: '0.05em' }}>
                  ANALYSIS TERMINAL
                </span>
              </div>
              {/* Terminal body */}
              <div ref={terminalRef} style={{
                padding: '10px 14px', maxHeight: '180px', overflowY: 'auto',
                display: 'flex', flexDirection: 'column', gap: '3px',
                fontFamily: 'var(--font-mono)', fontSize: '11px', lineHeight: '1.6',
              }}>
                {logs.map((log, i) => (
                  <div key={i} style={{
                    color: i >= prevLogCount ? 'var(--color-text)' : 'var(--color-text-faint)',
                    opacity: i >= prevLogCount ? 1 : 0.7,
                    animation: i >= prevLogCount ? 'logFadeIn 200ms ease forwards' : 'none',
                  }}>
                    <span style={{ color: '#28ca41', marginRight: '6px', fontWeight: 700 }}>❯</span>
                    {log}
                  </div>
                ))}
                {logs.length === 0 && (
                  <div style={{ color: 'var(--color-text-faint)' }}>
                    <span style={{ color: '#28ca41', marginRight: '6px', fontWeight: 700 }}>❯</span>
                    Initializing analysis pipeline...
                  </div>
                )}
              </div>
            </div>

            {result?.status === 'failed' && (
              <>
                <p className="error-msg">{result.error ?? 'Job failed'}</p>
                <NeuralButton onClick={handleReset}>Retry</NeuralButton>
              </>
            )}
            {result?.status !== 'failed' && (
              <NeuralButton variant="ghost" onClick={handleReset}>Cancel</NeuralButton>
            )}
          </div>
        </div>
      )}

      {/* STATE 4: RESULTS */}
      {stage === 'results' && result?.summary && (
        <>
          {/* KPI Cards */}
          <div className="kpi-grid">
            <div className="card kpi-card kpi-card--total" style={{ textAlign: 'center' }}>
              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '6px' }}><Icon3DTotal size={20} /></div>
              <div className="kpi-card__tag" style={{ textAlign: 'center' }}>Total</div>
              <div className="kpi-card__value" style={{ textAlign: 'center' }}>{result.summary.total_analyzed}</div>
              <div className="kpi-card__sub" style={{ textAlign: 'center' }}>reviews</div>
            </div>
            <div className="card kpi-card kpi-card--positive" style={{ textAlign: 'center' }}>
              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '6px' }}><Icon3DPositive size={20} /></div>
              <div className="kpi-card__tag" style={{ textAlign: 'center' }}>Positive</div>
              <div className="kpi-card__value" style={{ textAlign: 'center' }}>{result.summary.positive_pct}%</div>
              <div className="kpi-card__sub" style={{ textAlign: 'center' }}>{result.summary.positive} reviews</div>
            </div>
            <div className="card kpi-card kpi-card--negative" style={{ textAlign: 'center' }}>
              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '6px' }}><Icon3DNegative size={20} /></div>
              <div className="kpi-card__tag" style={{ textAlign: 'center' }}>Negative</div>
              <div className="kpi-card__value" style={{ textAlign: 'center' }}>{result.summary.negative_pct}%</div>
              <div className="kpi-card__sub" style={{ textAlign: 'center' }}>{result.summary.negative} reviews</div>
            </div>
            <div className="card kpi-card kpi-card--neutral" style={{ textAlign: 'center' }}>
              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '6px' }}><Icon3DNeutral size={20} /></div>
              <div className="kpi-card__tag" style={{ textAlign: 'center' }}>Neutral</div>
              <div className="kpi-card__value" style={{ textAlign: 'center' }}>{result.summary.neutral_pct}%</div>
              <div className="kpi-card__sub" style={{ textAlign: 'center' }}>{result.summary.neutral} reviews</div>
            </div>
            <div className="card kpi-card kpi-card--sarcasm" style={{ textAlign: 'center' }}>
              <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '6px' }}><Icon3DSarcasm size={20} /></div>
              <div className="kpi-card__tag" style={{ textAlign: 'center' }}>Sarcasm</div>
              <div className="kpi-card__value" style={{ textAlign: 'center' }}>{result.summary.sarcasm_count}</div>
              <div className="kpi-card__sub" style={{ textAlign: 'center' }}>flagged</div>
            </div>
          </div>

          {/* Results Table */}
          <div className="card animate-in card--animated" style={{ marginTop: 'var(--space-4)' }}>
            <SectionHeader icon={<Icon3DResults size={22} />} title="Results" subtitle="Per-review analysis output" />
            <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '0 var(--space-4)' }}>
              <NeuralButton variant="ghost" size="sm" onClick={() => setShowAll(!showAll)}>
                {showAll ? 'Show Less' : 'Show All'}
              </NeuralButton>
            </div>
            <div className="results-table-wrap">
              <table className="results-table">
                <thead><tr>
                  <th style={{ textAlign: 'center' }}>#</th>
                  <th style={{ textAlign: 'center' }}>Review Text</th>
                  <th style={{ textAlign: 'center' }}>Sentiment</th>
                  <th style={{ textAlign: 'center' }}>Confidence</th>
                  <th style={{ textAlign: 'center' }}>Polarity</th>
                  {isMultilingual && <th style={{ textAlign: 'center' }}>Language</th>}
                  {isMultilingual && <th style={{ textAlign: 'center' }}>Translation</th>}
                  <th style={{ textAlign: 'center' }}>Sarcasm</th>
                </tr></thead>
                <tbody>
                  {displayRows.map(row => (
                    <tr key={row.row_index}>
                      <td className="col-idx" style={{ textAlign: 'center' }}>{row.row_index}</td>
                      <td className="col-text" title={row.text} style={{ textAlign: 'center' }}>
                        {row.text.slice(0, 80)}{row.text.length > 80 ? '…' : ''}
                      </td>
                      <td style={{ textAlign: 'center' }}><SentimentBadge sentiment={row.sentiment} confidence={row.confidence} showConfidence={false} /></td>
                      <td className="col-num" style={{ textAlign: 'center' }}>
                        {/* GAP 1-D: show — instead of 0.0% for timeout/error rows */}
                        {row.sentiment === 'unknown' || row.sentiment === 'error'
                          ? '\u2014'
                          : `${row.confidence.toFixed(1)}%`}
                      </td>
                      <td className="col-num" style={{ textAlign: 'center' }}>{row.polarity.toFixed(3)}</td>
                      {isMultilingual && (
                        <td className="col-num" style={{ textAlign: 'center' }}>
                          {row.detected_language ?? '—'}
                        </td>
                      )}
                      {isMultilingual && (
                        <td className="col-num" style={{ textAlign: 'center' }}>
                          {row.translation_method ?? '—'}
                        </td>
                      )}
                      <td className="col-num" style={{ textAlign: 'center' }}>
                        {row.sarcasm_detected ? <span className="sarcasm-warn">!!</span> : '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {result.results && <AnalysisErrorSummary results={result.results} />}
          </div>

          {/* Charts Row */}
          <div className="chart-row" style={{ marginTop: 'var(--space-4)' }}>
            <div className="card animate-in">
              <SectionHeader icon={<Icon3DPie size={22} />} title="Sentiment Distribution" subtitle="Proportion of sentiments across reviews" />
              <div className="card-body">
                <SentimentPieChart
                  positive={result.summary.positive_pct}
                  negative={result.summary.negative_pct}
                  neutral={result.summary.neutral_pct} />
              </div>
            </div>
            <div className="card animate-in">
              <SectionHeader icon={<Icon3DKeyword size={22} />} title="Top Keywords" subtitle="Most frequent terms across reviews" />
              <div className="card-body">
                <TopKeywordsChart keywords={topKeywords} />
              </div>
            </div>
          </div>

          {/* Sentiment Trend */}
          {trendData && (
            <div className="card animate-in chart-full" style={{ marginTop: 'var(--space-4)' }}>
              <SectionHeader icon={<Icon3DTrend size={22} />} title="Sentiment Trend" subtitle="Simulated monthly sentiment distribution" />
              <div className="card-body">
                <SentimentTrendChart data={trendData} />
              </div>
            </div>
          )}

          {/* AI Summary */}
          <div className="card animate-in" style={{ marginTop: 'var(--space-4)' }}>
            <SectionHeader icon={<Icon3DRobot size={22} />} title="AI Summary" subtitle="AI-Generated analysis of the dataset" />
            <div className="ai-summary" style={{ textAlign: 'center' }}>
              <div className="ai-summary__item" style={{ justifyContent: 'center' }}>
                <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}>
                  <svg width="16" height="16" viewBox="0 0 48 48" style={icon3dStyle} fill="none">
                    <defs><linearGradient id="bs1" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#00FF88"/></linearGradient></defs>
                    <circle cx="24" cy="24" r="16" stroke="url(#bs1)" strokeWidth="2" fill="url(#bs1)" fillOpacity=".12" />
                    <circle cx="24" cy="24" r="6" fill="url(#bs1)" opacity=".4" />
                  </svg>
                </span>
                <span><strong>Overall:</strong> The dataset of {result.summary.total_analyzed} reviews shows a {result.summary.positive_pct > 50 ? 'predominantly positive' : 'mixed'} sentiment landscape.</span>
              </div>
              <div className="ai-summary__item" style={{ justifyContent: 'center' }}>
                <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}>
                  <svg width="16" height="16" viewBox="0 0 48 48" style={icon3dStyle} fill="none">
                    <defs><linearGradient id="bs2" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#22C55E"/><stop offset="100%" stopColor="#F43F5E"/></linearGradient></defs>
                    <rect x="8" y="8" width="32" height="32" rx="6" stroke="url(#bs2)" strokeWidth="2" fill="url(#bs2)" fillOpacity=".1" />
                    <path d="M16 24h16M24 16v16" stroke="url(#bs2)" strokeWidth="2" strokeLinecap="round" opacity=".6" />
                  </svg>
                </span>
                <span><strong>Distribution:</strong> {result.summary.positive_pct}% positive, {result.summary.negative_pct}% negative, {result.summary.neutral_pct}% neutral.</span>
              </div>
              <div className="ai-summary__item" style={{ justifyContent: 'center' }}>
                <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}>
                  <svg width="16" height="16" viewBox="0 0 48 48" style={icon3dStyle} fill="none">
                    <defs><linearGradient id="bs3" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#FDE047"/><stop offset="100%" stopColor="#F59E0B"/></linearGradient></defs>
                    <circle cx="24" cy="24" r="16" stroke="url(#bs3)" strokeWidth="2" fill="none" />
                    <circle cx="24" cy="24" r="8" stroke="url(#bs3)" strokeWidth="1.5" fill="url(#bs3)" fillOpacity=".15" />
                    <circle cx="24" cy="24" r="3" fill="url(#bs3)" />
                  </svg>
                </span>
                <span><strong>Model Confidence:</strong> Average confidence {result.results ? (result.results.reduce((s, r) => s + r.confidence, 0) / result.results.length).toFixed(1) : '—'}%.</span>
              </div>
              <div className="ai-summary__item" style={{ justifyContent: 'center' }}>
                <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}>
                  <svg width="16" height="16" viewBox="0 0 48 48" style={icon3dStyle} fill="none">
                    <defs><linearGradient id="bs4" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#A78BFA"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs>
                    <path d="M24 8L40 38H8z" stroke="url(#bs4)" strokeWidth="2" fill="url(#bs4)" fillOpacity=".15" strokeLinejoin="round" />
                  </svg>
                </span>
                <span><strong>Polarity Score:</strong> Mean polarity is {result.results ? (result.results.reduce((s, r) => s + r.polarity, 0) / result.results.length).toFixed(3) : '—'} ({result.summary.positive_pct > 50 ? 'positive' : 'balanced'} overall).</span>
              </div>
              <div className="ai-summary__item" style={{ justifyContent: 'center' }}>
                <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}>
                  <svg width="16" height="16" viewBox="0 0 48 48" style={icon3dStyle} fill="none">
                    <defs><linearGradient id="bs5" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#00FF88"/></linearGradient></defs>
                    <circle cx="24" cy="24" r="18" stroke="url(#bs5)" strokeWidth="2" fill="url(#bs5)" fillOpacity=".08" />
                    <ellipse cx="24" cy="24" rx="8" ry="18" stroke="url(#bs5)" strokeWidth="1.5" fill="none" />
                    <path d="M6 24h36" stroke="url(#bs5)" strokeWidth="1" opacity=".5" />
                  </svg>
                </span>
                <span><strong>Language Diversity:</strong> Primary language: English.</span>
              </div>
              <div className="ai-summary__item" style={{ justifyContent: 'center' }}>
                <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}>
                  <svg width="16" height="16" viewBox="0 0 48 48" style={icon3dStyle} fill="none">
                    <defs><linearGradient id="bs6" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#A78BFA"/><stop offset="100%" stopColor="#F43F5E"/></linearGradient></defs>
                    <path d="M24 4L6 14v12c0 12 8 16 18 18 10-2 18-6 18-18V14L24 4z" stroke="url(#bs6)" strokeWidth="2" fill="url(#bs6)" fillOpacity=".1" />
                    <path d="M24 18v8M24 30v2" stroke="url(#bs6)" strokeWidth="2" strokeLinecap="round" />
                  </svg>
                </span>
                <span><strong>Sarcasm:</strong> {result.summary.sarcasm_count} reviews ({result.summary.total_analyzed > 0 ? ((result.summary.sarcasm_count / result.summary.total_analyzed) * 100).toFixed(1) : 0}%) flagged as sarcastic.</span>
              </div>
              <div className="ai-summary__item" style={{ justifyContent: 'center' }}>
                <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}>
                  <svg width="16" height="16" viewBox="0 0 48 48" style={icon3dStyle} fill="none">
                    <defs><linearGradient id="bs7" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#F43F5E"/><stop offset="100%" stopColor="#FDE047"/></linearGradient></defs>
                    <circle cx="24" cy="24" r="16" stroke="url(#bs7)" strokeWidth="2" fill="url(#bs7)" fillOpacity=".1" />
                    <path d="M24 16v10M24 30v2" stroke="url(#bs7)" strokeWidth="2.5" strokeLinecap="round" />
                  </svg>
                </span>
                <span><strong>Action Required:</strong> {result.summary.negative} negative reviews detected — recommended for priority review.</span>
              </div>
            </div>
          </div>

          {/* Export Results */}
          <div className="card animate-in card--animated" style={{ marginTop: 'var(--space-4)' }}>
            <SectionHeader icon={<Icon3DSave size={22} />} title="Export Results" subtitle="Download analysis in multiple formats" />
            <div style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(4, 1fr)',
              gap: 'var(--space-3)',
              padding: 'var(--space-5)',
              borderTop: '1px solid var(--glass-border)',
            }}>
              <NeuralButton variant="secondary" size="sm" onClick={exportCSV} style={{ width: '100%', justifyContent: 'center' }}>📄 CSV</NeuralButton>
              <NeuralButton variant="secondary" size="sm" style={{ width: '100%', justifyContent: 'center' }}
                      onClick={exportPDF}>📑 PDF</NeuralButton>
              <NeuralButton variant="secondary" size="sm" style={{ width: '100%', justifyContent: 'center' }}
                      onClick={() => {
                        if (!result?.results || !result.summary) return
                        generateUniversalJSON({ rows: result.results, summary: result.summary, mode: 'bulk', filename: `reviewsense-bulk-${jobId ?? 'export'}.json` })
                        showToast('success', 'JSON exported successfully')
                      }}>{'{ }'} JSON</NeuralButton>
              <NeuralButton variant="secondary" size="sm" style={{ width: '100%', justifyContent: 'center' }}
                      onClick={exportExcel}>📊 Excel</NeuralButton>
            </div>
          </div>

          <div className="form-actions" style={{ justifyContent: 'center', marginTop: 'var(--space-4)' }}>
            <NeuralButton variant="ghost" onClick={handleReset}>Analyze Another File</NeuralButton>
          </div>
        </>
      )}

      {error && stage !== 'processing' && (
        <p className="error-msg" role="alert">{error}</p>
      )}
    </PageWrapper>
  )
}
