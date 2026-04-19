import { useState, useCallback, useRef, useEffect, useMemo, type CSSProperties } from 'react'
import { SentimentBadge, AnalysisErrorSummary } from '@/components/ui/Badge'
import { NeuralInputWrap } from '@/components/ui/NeuralInputWrap'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { NeuralButton } from '@/components/ui/NeuralButton'
import { EyebrowPill } from '@/components/ui/EyebrowPill'
import { HoloToggle } from '@/components/ui/HoloToggle'
import { FolderUpload } from '@/components/ui/FolderUpload'
import { CyberLoader } from '@/components/ui/CyberLoader'
import { CyberCard } from '@/components/ui/CyberCard'
import { SentimentPieChart } from '@/components/charts/SentimentPieChart'
import { TopKeywordsChart } from '@/components/charts/TopKeywordsChart'
import { SentimentTrendChart } from '@/components/charts/SentimentTrendChart'
import { useBulk } from '@/hooks/useBulk'
import { useBulkStore } from '@/hooks/useBulkStore'
import { useApp } from '@/context/AppContext'
import { pushTrendPoint } from '@/hooks/useTrendStore'
import { generateUniversalPDF, generateUniversalCSV, generateUniversalExcel, generateUniversalJSON } from '@/utils/exportUtils'

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

function Icon3DPulse({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="pls3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#2dd4bf"/></linearGradient></defs>
      <circle cx="24" cy="24" r="18" stroke="url(#pls3d)" strokeWidth="1.5" fill="url(#pls3d)" fillOpacity=".08" />
      <path d="M8 24h8l4-12 4 24 4-12 4 6 4-6h8" stroke="url(#pls3d)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}



function Icon3DSentimentPie({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="spie3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#22C55E"/><stop offset="100%" stopColor="#F59E0B"/></linearGradient></defs>
      <circle cx="24" cy="24" r="18" stroke="url(#spie3d)" strokeWidth="2" fill="url(#spie3d)" fillOpacity=".08" />
      <path d="M24 6v18l14 10" stroke="url(#spie3d)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M24 24L10 14" stroke="url(#spie3d)" strokeWidth="1.5" strokeLinecap="round" opacity=".5" />
    </svg>
  )
}

function Icon3DGearPanel({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="gp3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#A78BFA"/><stop offset="100%" stopColor="#818cf8"/></linearGradient></defs>
      <path d="M24 16a8 8 0 100 16 8 8 0 000-16z" stroke="url(#gp3d)" strokeWidth="2" fill="url(#gp3d)" fillOpacity=".15" />
      <path d="M24 4v6M24 38v6M4 24h6M38 24h6M9.9 9.9l4.2 4.2M33.9 33.9l4.2 4.2M38.1 9.9l-4.2 4.2M14.1 33.9l-4.2 4.2" stroke="url(#gp3d)" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

/** Styled sub-box panel header with icon + title */
function PanelBadge({ icon, label, bg, border, color }: {
  icon: React.ReactNode, label: string,
  bg: string, border: string, color: string,
}) {
  return (
    <div style={{
      display: 'inline-flex', alignItems: 'center', gap: '7px', alignSelf: 'center',
      background: bg, border: `1px solid ${border}`,
      borderRadius: '10px', padding: '5px 14px',
      marginBottom: '10px',
    }}>
      {icon}
      <span style={{
        fontSize: '10px', fontWeight: 700,
        textTransform: 'uppercase', letterSpacing: '0.08em',
        color,
      }}>{label}</span>
    </div>
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

function Icon3DTarget({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="btgt3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#F43F5E"/><stop offset="100%" stopColor="#FDE047"/></linearGradient></defs>
      <circle cx="24" cy="24" r="18" stroke="url(#btgt3d)" strokeWidth="2" fill="none" />
      <circle cx="24" cy="24" r="12" stroke="url(#btgt3d)" strokeWidth="1.5" fill="url(#btgt3d)" fillOpacity=".06" />
      <circle cx="24" cy="24" r="5" fill="url(#btgt3d)" opacity=".35" />
      <circle cx="24" cy="24" r="2" fill="url(#btgt3d)" />
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
  if (s === 'LinearSVC') return 'Linear SVC'
  // Only split at camelCase boundaries: uppercase preceded by lowercase
  return s
    .replace(/([a-z])([A-Z])/g, '$1 $2')
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
  const { showToast, state: appState } = useApp()
  const { confidenceThreshold } = appState
  const store = useBulkStore()
  const {
    stage, setStage, fileName, setFileName, textColumn, setTextColumn,
    model, setModel, runAbsa, setRunAbsa, runSarcasm, setRunSarcasm,
    isMultilingual, setIsMultilingual, showAll, setShowAll,
    startedAt, setStartedAt, logs, setLogs,
    jobId: storedJobId, setJobId: setStoredJobId,
    result: storedResult, setResult: setStoredResult,
    columns: storedColumns, setColumns: setStoredColumns,
    preview: storedPreview, setPreview: setStoredPreview,
    reset: resetStore,
  } = store

  // File object is local (can't persist in ref) — only fileName is persisted
  const [file, setFile] = useState<File | null>(null)
  const [prevLogCount, setPrevLogCount] = useState(0)

  // Timer: tick a local `now` state every second while processing.
  // Elapsed is derived from the persisted startedAt timestamp,
  // so it is always accurate — even after navigating away and back.
  const [_now, setNow] = useState(Date.now())
  useEffect(() => {
    if (stage !== 'processing') return
    const h = setInterval(() => setNow(Date.now()), 1000)
    return () => clearInterval(h)
  }, [stage])
  const elapsed = startedAt ? Math.floor((_now - startedAt) / 1000) : 0

  const {
    result: bulkResult, error, columns: bulkColumns,
    preview: bulkPreview, submit, reset: bulkReset,
    previewColumns, resumePolling,
  } = useBulk()
  const terminalRef = useRef<HTMLDivElement>(null)

  // Effective values: prefer live bulk hook data, fall back to stored
  const result = bulkResult || storedResult
  const columns = bulkColumns.length > 0 ? bulkColumns : storedColumns
  const preview = bulkPreview.length > 0 ? bulkPreview : storedPreview
  const jobId = storedJobId

  // Sync useBulk results into the store
  useEffect(() => {
    if (bulkResult) setStoredResult(bulkResult)
  }, [bulkResult, setStoredResult])
  useEffect(() => {
    if (bulkColumns.length > 0) setStoredColumns(bulkColumns)
  }, [bulkColumns, setStoredColumns])
  useEffect(() => {
    if (bulkPreview.length > 0) setStoredPreview(bulkPreview)
  }, [bulkPreview, setStoredPreview])

  // Resume polling on remount if job was in-progress (Scenario A)
  const hasResumed = useRef(false)
  useEffect(() => {
    if (hasResumed.current) return
    if (stage === 'processing' && storedJobId) {
      hasResumed.current = true
      resumePolling(storedJobId)
    }
    // Scenario B: was in configure but file is gone
    if (stage === 'configure' && !file && !storedJobId) {
      // Keep stage as configure — the UI will show a notice to re-upload
    }
    // Scenario C: results stage — storedResult is already loaded, nothing to do
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (stage === 'processing') {
      // Only reset logs if this is a fresh start (not a resume)
      if (!hasResumed.current || !startedAt) {
        setLogs(['Starting analysis pipeline...'])
      }
      // startedAt is set in handleSubmit — no timer to manage here
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [stage])

  // Use real backend logs — delivered per-row via polling
  useEffect(() => {
    if (stage === 'processing' && result?.logs && result.logs.length > 0) {
      setLogs(result.logs)
    }
  }, [result?.logs, stage, setLogs])

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
    if (result?.status === 'completed' && stage === 'processing') {
      // Push completed batch to the global trend store
      if (result.results && result.results.length > 0) {
        pushTrendPoint(result.results)
      }
      setStage('results')
    }
    if (result?.status === 'failed' && stage === 'processing') {
      // Keep showing processing view with error — don't transition
    }
  }, [result?.status, result?.results, stage, setStage])

  const handleFileSelect = useCallback(async (f: File) => {
    setFile(f)
    setFileName(f.name)
    const cols = await previewColumns(f)
    if (cols.length > 0) { setTextColumn(cols[0]); setStage('configure') }
  }, [previewColumns, setFileName, setTextColumn, setStage])

  const handleSubmit = useCallback(async () => {
    if (!file) return
    hasResumed.current = false
    setStage('processing')
    setStartedAt(Date.now())
    setStoredJobId(null)  // will be set by useBulk
    await submit(file, textColumn, model, runAbsa, runSarcasm, isMultilingual)
  }, [file, textColumn, model, runAbsa, runSarcasm, isMultilingual, submit, setStage, setStartedAt, setStoredJobId])

  // Sync jobId from useBulk into store
  useEffect(() => {
    if (bulkResult?.job_id && bulkResult.job_id !== storedJobId) {
      setStoredJobId(bulkResult.job_id)
    }
  }, [bulkResult?.job_id, storedJobId, setStoredJobId])

  const handleReset = useCallback(() => {
    bulkReset()
    resetStore()
    setFile(null)
    hasResumed.current = false
  }, [bulkReset, resetStore])

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

  // Aggregate ABSA data from all bulk rows for the bulk ABSA overview
  const topAbsaAspects = useMemo(() => {
    if (!result?.results) return []
    const aspectMap: Record<string, { count: number; positive: number; negative: number; neutral: number; totalPolarity: number }> = {}
    result.results.forEach(row => {
      if (!row.aspects) return
      row.aspects.forEach(item => {
        const key = item.aspect.toLowerCase()
        if (!aspectMap[key]) aspectMap[key] = { count: 0, positive: 0, negative: 0, neutral: 0, totalPolarity: 0 }
        aspectMap[key].count++
        aspectMap[key].totalPolarity += item.polarity
        if (item.sentiment === 'positive') aspectMap[key].positive++
        else if (item.sentiment === 'negative') aspectMap[key].negative++
        else aspectMap[key].neutral++
      })
    })
    return Object.entries(aspectMap)
      .map(([aspect, d]) => ({
        aspect,
        count: d.count,
        positive: d.positive,
        negative: d.negative,
        neutral: d.neutral,
        avgPolarity: d.count > 0 ? d.totalPolarity / d.count : 0,
        dominantSentiment: d.positive >= d.negative && d.positive >= d.neutral
          ? 'positive'
          : d.negative >= d.positive && d.negative >= d.neutral
          ? 'negative'
          : 'neutral',
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10)
  }, [result?.results])

  const exportCSV = useCallback(() => {
    if (!result?.results || result.results.length === 0) { showToast('error', 'No results to export'); return }
    generateUniversalCSV({
      rows: result.results,
      mode: 'bulk',
      filename: `reviewsense-bulk-${jobId ?? 'export'}.csv`,
      absaAspects: runAbsa ? topAbsaAspects : undefined,
      sarcasmEnabled: runSarcasm,
      sarcasmCount: result.summary?.sarcasm_count,
    })
    showToast('success', 'CSV exported successfully')
  }, [result, jobId, showToast, runAbsa, runSarcasm, topAbsaAspects])

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
      absaAspects: runAbsa ? topAbsaAspects : undefined,
      sarcasmEnabled: runSarcasm,
    })
    showToast('success', 'PDF report downloaded')
  }, [result, jobId, topKeywords, trendData, showToast, runAbsa, runSarcasm, topAbsaAspects])

  const exportExcel = useCallback(() => {
    if (!result?.results || result.results.length === 0) { showToast('error', 'No results to export'); return }
    generateUniversalExcel({
      rows: result.results,
      mode: 'bulk',
      filename: `reviewsense-bulk-${jobId ?? 'export'}.xls`,
      absaAspects: runAbsa ? topAbsaAspects : undefined,
      sarcasmEnabled: runSarcasm,
      sarcasmCount: result.summary?.sarcasm_count,
    })
    showToast('success', 'Excel file downloaded')
  }, [result, jobId, showToast, runAbsa, runSarcasm, topAbsaAspects])

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
      {stage === 'configure' && (file ? (
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
            <NeuralButton size="lg" style={{ width: 'calc(100% - 8px)', justifyContent: 'center' }}
                    onClick={handleSubmit}>
              Analyze All Reviews
            </NeuralButton>
          </div>
        </>
      ) : (
        /* Scenario B: configure stage but file lost after navigation */
        <div className="card animate-in card--animated">
          <SectionHeader icon={<Icon3DFile size={22} />} title="File Selection Lost" subtitle="Your previous file selection was lost. Please re-upload your file." />
          <div className="card-body" style={{ textAlign: 'center' }}>
            {fileName && <div style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)', marginBottom: 'var(--space-3)' }}>Previous file: {fileName}</div>}
            <FolderUpload onFileSelect={handleFileSelect} />
          </div>
        </div>
      ))}

      {/* STATE 3: PROCESSING — 2×2 corner grid + centered loader */}
      {stage === 'processing' && (() => {
        // ── Live stats from streaming results (updates every 250ms poll) ──
        const rows = result?.results ?? []
        const processed = result?.processed ?? 0
        const total = result?.total_rows ?? 0
        const progressPct = total > 0 ? Math.round((processed / total) * 100) : 0
        const speed = elapsed > 0 ? (processed / elapsed).toFixed(1) : '0.0'
        const avgConf = rows.length > 0 ? (rows.reduce((s, r) => s + r.confidence, 0) / rows.length).toFixed(1) : '—'
        const errorCount = rows.filter(r => r.sentiment === 'error' || r.sentiment === 'unknown').length

        // ── Live sentiment distribution ──
        const posCount = rows.filter(r => r.sentiment === 'positive').length
        const negCount = rows.filter(r => r.sentiment === 'negative').length
        const neuCount = rows.filter(r => r.sentiment === 'neutral').length
        const sentRealTotal = posCount + negCount + neuCount
        const hasSentimentData = sentRealTotal > 0
        const sentTotal = sentRealTotal || 1
        const posPct = Math.round((posCount / sentTotal) * 100)
        const negPct = Math.round((negCount / sentTotal) * 100)
        const neuPct = 100 - posPct - negPct
        const sarcasmCount = rows.filter(r => r.sarcasm_detected).length



        // ── Shared styles ──
        const statLabel: React.CSSProperties = {
          fontSize: '10px', color: 'var(--color-text-faint)',
          textTransform: 'uppercase', letterSpacing: '0.06em',
        }
        const statValue: React.CSSProperties = {
          fontSize: '13px', fontWeight: 700, fontFamily: 'var(--font-mono)',
          color: 'var(--color-text)', transition: 'all 0.3s ease',
        }

        return (
        <div className="card animate-in" style={{ padding: '16px' }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: '190px 1fr 190px',
            gridTemplateRows: '1fr 1fr',
            gap: '12px',
          }}>

            {/* ── TOP-LEFT: Live Stats ── */}
            <CyberCard style={{ gridColumn: 1, gridRow: 1 }}>
              <PanelBadge icon={<Icon3DPulse />} label="Live Stats"
                bg="rgba(0,217,255,0.06)" border="rgba(0,217,255,0.18)" color="#00d9ff" />
              <div style={{ display: 'flex', flexDirection: 'column', gap: '7px', flex: 1, justifyContent: 'center' }}>
                {[
                  { label: 'Processed', value: `${processed} / ${total || '?'}`, color: 'var(--color-primary-bright)' },
                  { label: 'Speed', value: `${speed} r/s`, color: '#2dd4bf' },
                  { label: 'Avg Conf', value: avgConf === '—' ? '—' : `${avgConf}%`, color: '#a78bfa' },
                  { label: 'Errors', value: String(errorCount), color: errorCount > 0 ? 'var(--color-negative)' : 'var(--color-positive)' },
                  { label: 'Progress', value: `${progressPct}%`, color: '#fde047' },
                ].map(s => (
                  <div key={s.label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span style={statLabel}>{s.label}</span>
                    <span style={{ ...statValue, color: s.color }}>{s.value}</span>
                  </div>
                ))}
              </div>
            </CyberCard>

            {/* ── TOP-RIGHT: Sentiment ── */}
            <CyberCard style={{ gridColumn: 3, gridRow: 1 }}>
              <PanelBadge icon={<Icon3DSentimentPie />} label="Sentiment"
                bg="rgba(34,197,94,0.06)" border="rgba(34,197,94,0.18)" color="#22c55e" />
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', flex: 1, justifyContent: 'center' }}>
                {hasSentimentData ? (
                  <>
                    <div style={{
                      width: '68px', height: '68px', borderRadius: '50%',
                      background: `conic-gradient(
                        #22c55e 0% ${posPct}%,
                        #f59e0b ${posPct}% ${posPct + neuPct}%,
                        #f43f5e ${posPct + neuPct}% 100%
                      )`,
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      transition: 'all 0.3s ease',
                    }}>
                      <div style={{
                        width: '44px', height: '44px', borderRadius: '50%',
                        background: 'var(--color-bg-card, #0f1923)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                        fontSize: '11px', fontWeight: 700, color: 'var(--color-text)',
                        fontFamily: 'var(--font-mono)',
                      }}>
                        {sentRealTotal}
                      </div>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', width: '100%' }}>
                      {[
                        { label: 'Positive', pct: posPct, color: '#22c55e' },
                        { label: 'Neutral', pct: neuPct, color: '#f59e0b' },
                        { label: 'Negative', pct: negPct, color: '#f43f5e' },
                      ].map(s => (
                        <div key={s.label}>
                          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', marginBottom: '2px' }}>
                            <span style={{ color: s.color, fontWeight: 600 }}>{s.label}</span>
                            <span style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>{s.pct}%</span>
                          </div>
                          <div style={{ height: '3px', borderRadius: '2px', background: 'rgba(255,255,255,0.06)' }}>
                            <div style={{
                              height: '100%', borderRadius: '2px', background: s.color,
                              width: `${s.pct}%`, transition: 'width 0.4s ease', opacity: 0.8,
                            }} />
                          </div>
                        </div>
                      ))}
                    </div>
                  </>
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '10px', padding: '12px 0', flex: 1 }}>
                    <div style={{
                      width: '48px', height: '48px', borderRadius: '50%',
                      border: '2px dashed rgba(34,197,94,0.3)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      animation: 'pulse 2s ease-in-out infinite',
                    }}>
                      <div style={{
                        fontSize: '11px', fontWeight: 700, color: 'var(--color-text-faint)',
                        fontFamily: 'var(--font-mono)',
                      }}>0</div>
                    </div>
                    <div style={{ fontSize: '10px', color: 'var(--color-text-faint)', textAlign: 'center', lineHeight: 1.4, letterSpacing: '0.02em' }}>
                      Awaiting data…
                    </div>
                  </div>
                )}
              </div>
            </CyberCard>

            {/* ── BOTTOM-LEFT: Config ── */}
            <CyberCard style={{ gridColumn: 1, gridRow: 2, opacity: 0.85 }}>
              <PanelBadge icon={<Icon3DGearPanel />} label="Config"
                bg="rgba(167,139,250,0.06)" border="rgba(167,139,250,0.18)" color="#a78bfa" />
              <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '11px', flex: 1, justifyContent: 'center' }}>
                {[
                  ['Model', model === 'best' ? 'Best' : formatModelName(model)],
                  ['Multi', isMultilingual ? 'ON' : 'OFF'],
                  ['ABSA', runAbsa ? 'ON' : 'OFF'],
                  ['Sarcasm', runSarcasm ? 'ON' : 'OFF'],
                ].map(([k, v]) => (
                  <div key={k} style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <span style={{ color: 'var(--color-text-faint)' }}>{k}</span>
                    <span style={{
                      fontWeight: 600, fontFamily: 'var(--font-mono)',
                      color: v === 'ON' ? 'var(--color-positive)' : v === 'OFF' ? 'var(--color-text-faint)' : 'var(--color-primary-bright)',
                    }}>{v}</span>
                  </div>
                ))}
              </div>
            </CyberCard>

            {/* ── BOTTOM-RIGHT: Pipeline (with real-time counts) ── */}
            <CyberCard style={{ gridColumn: 3, gridRow: 2, opacity: 0.85 }}>
              <PanelBadge icon={<Icon3DPulse />} label="Pipeline"
                bg="rgba(0,217,255,0.06)" border="rgba(0,217,255,0.18)" color="#00d9ff" />
              <div style={{ display: 'flex', flexDirection: 'column', gap: '6px', fontSize: '11px', flex: 1, justifyContent: 'center' }}>
                {hasSentimentData ? (
                  [
                    { label: 'Positive', value: posCount, color: '#22c55e' },
                    { label: 'Neutral', value: neuCount, color: '#f59e0b' },
                    { label: 'Negative', value: negCount, color: '#f43f5e' },
                    { label: 'Sarcasm', value: sarcasmCount, color: '#a78bfa' },
                  ].map(s => (
                    <div key={s.label} style={{ display: 'flex', justifyContent: 'space-between' }}>
                      <span style={{ color: 'var(--color-text-faint)' }}>{s.label}</span>
                      <span style={{ fontWeight: 600, fontFamily: 'var(--font-mono)', color: s.color, transition: 'all 0.3s ease' }}>{s.value}</span>
                    </div>
                  ))
                ) : (
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '10px', padding: '12px 0', flex: 1 }}>
                    <div style={{
                      width: '48px', height: '48px', borderRadius: '50%',
                      border: '2px dashed rgba(0,217,255,0.3)',
                      display: 'flex', alignItems: 'center', justifyContent: 'center',
                      animation: 'pulse 2s ease-in-out infinite',
                    }}>
                      <div style={{
                        fontSize: '11px', fontWeight: 700, color: 'var(--color-text-faint)',
                        fontFamily: 'var(--font-mono)',
                      }}>0</div>
                    </div>
                    <div style={{ fontSize: '10px', color: 'var(--color-text-faint)', textAlign: 'center', lineHeight: 1.4, letterSpacing: '0.02em' }}>
                      Awaiting data…
                    </div>
                  </div>
                )}
              </div>
            </CyberCard>

            {/* ── CENTER: Loader + Terminal (spans both rows) ── */}
            <div style={{
              gridColumn: 2, gridRow: '1 / 3',
              display: 'flex', flexDirection: 'column',
              alignItems: 'center', justifyContent: 'center',
              gap: '6px',
            }}>
              {/* Cyber loader — scaled to fit center */}
              <div style={{ margin: '-85px 0 -40px 0', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                <CyberLoader scale={0.85} />
              </div>

              {/* Progress bar */}
              <div style={{ width: '80%', maxWidth: '300px', alignSelf: 'center' }}>
                <div style={{
                  height: '4px', borderRadius: '2px',
                  background: 'rgba(255,255,255,0.06)',
                  overflow: 'hidden',
                }}>
                  <div style={{
                    height: '100%', borderRadius: '2px',
                    background: 'linear-gradient(90deg, #00d9ff, #00ff88)',
                    width: `${progressPct}%`,
                    transition: 'width 0.4s ease',
                  }} />
                </div>
              </div>

              {/* Status pill */}
              <div style={{
                display: 'inline-flex', alignItems: 'center', gap: '8px',
                background: 'rgba(0, 217, 255, 0.06)', border: '1px solid rgba(0, 217, 255, 0.15)',
                borderRadius: '12px', padding: '5px 14px',
                whiteSpace: 'nowrap', marginTop: '6px',
              }}>
                <span style={{ fontSize: '11px', color: 'var(--color-primary-bright)', fontWeight: 600 }}>
                  {result?.status === 'failed' ? 'Analysis Failed' : 'Analyzing Reviews'}
                </span>
                <span style={{ fontSize: '10px', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>
                  {processed}/{total || '?'} · {Math.floor(elapsed / 60)}m {elapsed % 60}s
                </span>
              </div>

              {/* Terminal logs */}
              <div style={{
                width: '90%', maxWidth: '380px',
                background: 'rgba(0, 0, 0, 0.4)', border: '1px solid rgba(0, 217, 255, 0.1)',
                borderRadius: '10px', overflow: 'hidden',
              }}>
                <div style={{
                  display: 'flex', alignItems: 'center', gap: '5px',
                  padding: '5px 10px', borderBottom: '1px solid rgba(255,255,255,0.06)',
                  background: 'rgba(0,0,0,0.3)',
                }}>
                  <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#ff5f57' }} />
                  <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#ffbd2e' }} />
                  <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#28ca41' }} />
                  <span style={{ flex: 1, textAlign: 'center', fontSize: '8px', color: 'var(--color-text-faint)', fontFamily: 'var(--font-mono)', letterSpacing: '0.05em' }}>
                    ANALYSIS TERMINAL
                  </span>
                </div>
                <div ref={terminalRef} style={{
                  padding: '6px 10px', height: '90px', overflowY: 'auto',
                  display: 'flex', flexDirection: 'column', gap: '2px',
                  fontFamily: 'var(--font-mono)', fontSize: '9px', lineHeight: '1.5',
                }}>
                  {logs.map((log, i) => (
                    <div key={i} style={{
                      color: i >= prevLogCount ? 'var(--color-text)' : 'var(--color-text-faint)',
                      opacity: i >= prevLogCount ? 1 : 0.7,
                      animation: i >= prevLogCount ? 'logFadeIn 200ms ease forwards' : 'none',
                    }}>
                      <span style={{ color: '#28ca41', marginRight: '4px', fontWeight: 700 }}>❯</span>
                      {log}
                    </div>
                  ))}
                  {logs.length === 0 && (
                    <div style={{ color: 'var(--color-text-faint)' }}>
                      <span style={{ color: '#28ca41', marginRight: '4px', fontWeight: 700 }}>❯</span>
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
                <NeuralButton variant="ghost" size="sm" onClick={handleReset}>Cancel</NeuralButton>
              )}
            </div>

          </div>
        </div>
        )
      })()}

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
                  <th style={{ textAlign: 'center' }}>{isMultilingual ? 'Review Text (English)' : 'Review Text'}</th>
                  <th style={{ textAlign: 'center' }}>Sentiment</th>
                  <th style={{ textAlign: 'center' }}>Confidence</th>
                  <th style={{ textAlign: 'center' }}>Polarity</th>
                  {isMultilingual && <th style={{ textAlign: 'center' }}>Language</th>}
                  {isMultilingual && <th style={{ textAlign: 'center' }}>Translation</th>}
                </tr></thead>
                <tbody>
                  {displayRows.map(row => {
                    const belowThreshold = row.confidence < confidenceThreshold * 100
                    return (
                    <tr key={row.row_index} style={belowThreshold ? { opacity: 0.5 } : undefined}>
                      <td className="col-idx" style={{ textAlign: 'center' }}>{row.row_index}</td>
                      <td className="col-text" title={isMultilingual && row.translated_text ? row.translated_text : row.text} style={{ textAlign: 'center' }}>
                        {isMultilingual && row.translated_text
                          ? (row.translated_text.slice(0, 80) + (row.translated_text.length > 80 ? '\u2026' : ''))
                          : (row.text.slice(0, 80) + (row.text.length > 80 ? '\u2026' : ''))}
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
                          {row.detected_language ?? '\u2014'}
                        </td>
                      )}
                      {isMultilingual && (
                        <td className="col-num" style={{ textAlign: 'center' }}>
                          {row.translation_method ?? '\u2014'}
                        </td>
                      )}
                    </tr>
                    )
                  })}
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
              <SectionHeader icon={<Icon3DTrend size={22} />} title="Sentiment Trend" subtitle="Batch processing sentiment distribution" />
              <div className="card-body">
                <SentimentTrendChart data={trendData} />
              </div>
            </div>
          )}

          {/* ABSA Aggregation (only when runAbsa was enabled) */}
          {runAbsa && topAbsaAspects.length > 0 && (
            <div className="card animate-in card--animated" style={{ marginTop: 'var(--space-4)' }}>
              <SectionHeader icon={<Icon3DTarget size={22} />} title="Aspect-Based Sentiment Analysis" subtitle={`Top ${topAbsaAspects.length} aspects across ${result?.summary?.total_analyzed ?? 0} reviews`} />
              <div className="card-body">
                <table className="absa-table">
                  <thead><tr>
                    <th>Aspect</th>
                    <th>Mentions</th>
                    <th>Dominant</th>
                    <th>Positive</th>
                    <th>Negative</th>
                    <th>Neutral</th>
                    <th>Avg Polarity</th>
                  </tr></thead>
                  <tbody>
                    {topAbsaAspects.map((item, i) => (
                      <tr key={i} style={{ animationDelay: `${i * 0.04}s` }} className="animate-in">
                        <td className="absa-aspect-term">{item.aspect}</td>
                        <td style={{ fontFamily: 'var(--font-mono)', textAlign: 'center' }}>{item.count}</td>
                        <td style={{ textAlign: 'center' }}>
                          <span className={`badge badge--${item.dominantSentiment}`}>{item.dominantSentiment}</span>
                        </td>
                        <td style={{ textAlign: 'center', color: 'var(--color-positive)', fontFamily: 'var(--font-mono)' }}>{item.positive}</td>
                        <td style={{ textAlign: 'center', color: 'var(--color-negative)', fontFamily: 'var(--font-mono)' }}>{item.negative}</td>
                        <td style={{ textAlign: 'center', color: 'var(--color-neutral-sent)', fontFamily: 'var(--font-mono)' }}>{item.neutral}</td>
                        <td style={{ textAlign: 'center' }}>
                          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}>
                            <div className="prog-bar" style={{ width: '60px' }}>
                              <div
                                className={`prog-bar__fill prog-bar__fill--${item.avgPolarity >= 0 ? 'positive' : 'negative'}`}
                                style={{ width: `${Math.abs(item.avgPolarity) * 100}%` }}
                              />
                            </div>
                            <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', minWidth: '46px' }}>
                              {item.avgPolarity >= 0 ? '+' : ''}{item.avgPolarity.toFixed(3)}
                            </span>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
          {runAbsa && topAbsaAspects.length === 0 && result?.results && result.results.length > 0 && (
            <div className="card card--animated" style={{ marginTop: 'var(--space-4)', textAlign: 'center' }}>
              <SectionHeader icon={<Icon3DTarget size={22} />} title="Aspect-Based Sentiment Analysis" subtitle="No aspect data in results" />
              <p className="helper-text" style={{ padding: 'var(--space-5)' }}>ABSA was enabled but no aspects were extracted. Try more descriptive reviews.</p>
            </div>
          )}

          {/* Sarcasm Summary — dataset-level card, only when runSarcasm is ON */}
          {runSarcasm && (
            <div className="card animate-in card--animated" style={{ marginTop: 'var(--space-4)' }}>
              <SectionHeader icon={<Icon3DSarcasm size={22} />} title="Sarcasm Detection Summary" subtitle="Dataset-level sarcasm analysis" />
              <div className="card-body">
                {(result?.summary?.sarcasm_count ?? 0) > 0 ? (
                  <div style={{
                    display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--space-3)',
                    padding: 'var(--space-4)',
                  }}>
                    <div style={{
                      display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--space-2)',
                      padding: 'var(--space-4) var(--space-6)',
                      background: 'rgba(244,63,94,0.08)',
                      border: '1px solid rgba(244,63,94,0.25)',
                      borderRadius: '12px',
                      textAlign: 'center',
                    }}>
                      <svg width="36" height="36" viewBox="0 0 48 48" style={icon3dStyle} fill="none">
                        <defs><linearGradient id="sarc-warn" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#F43F5E"/><stop offset="100%" stopColor="#FDE047"/></linearGradient></defs>
                        <path d="M24 6L44 40H4z" stroke="url(#sarc-warn)" strokeWidth="2" fill="url(#sarc-warn)" fillOpacity=".12" strokeLinejoin="round"/>
                        <path d="M24 18v10M24 33v2" stroke="url(#sarc-warn)" strokeWidth="2.5" strokeLinecap="round"/>
                      </svg>
                      <div style={{ fontSize: 'var(--text-lg)', fontWeight: 700, color: 'var(--color-negative)' }}>
                        {result.summary.sarcasm_count} review{result.summary.sarcasm_count !== 1 ? 's' : ''} detected as sarcastic
                      </div>
                      <div style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)' }}>
                        {result.summary.total_analyzed > 0
                          ? `${((result.summary.sarcasm_count / result.summary.total_analyzed) * 100).toFixed(1)}% of the dataset — these reviews may mislead sentiment analysis`
                          : 'Sarcasm detected in this dataset'}
                      </div>
                    </div>
                    <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-faint)', textAlign: 'center', maxWidth: '480px' }}>
                      Sarcastic reviews are flagged by the <strong>!! indicator</strong> in the results table above. Consider excluding or re-weighting them for downstream tasks.
                    </div>
                  </div>
                ) : (
                  <div style={{
                    display: 'flex', flexDirection: 'column', alignItems: 'center',
                    padding: 'var(--space-5)',
                  }}>
                    <div style={{
                      display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--space-2)',
                      padding: 'var(--space-4) var(--space-6)',
                      background: 'rgba(34,197,94,0.08)',
                      border: '1px solid rgba(34,197,94,0.2)',
                      borderRadius: '12px',
                      textAlign: 'center',
                    }}>
                      <svg width="36" height="36" viewBox="0 0 48 48" style={icon3dStyle} fill="none">
                        <defs><linearGradient id="sarc-ok" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#22C55E"/><stop offset="100%" stopColor="#2DD4BF"/></linearGradient></defs>
                        <circle cx="24" cy="24" r="18" stroke="url(#sarc-ok)" strokeWidth="2" fill="url(#sarc-ok)" fillOpacity=".1"/>
                        <path d="M14 24l8 8 12-14" stroke="url(#sarc-ok)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                      </svg>
                      <div style={{ fontSize: 'var(--text-lg)', fontWeight: 700, color: 'var(--color-positive)' }}>
                        No Sarcasm Detected
                      </div>
                      <div style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)' }}>
                        All processed reviews show consistent linguistic patterns — sentiment predictions are stable and reliable.
                      </div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* AI Summary */}
          <div className="card animate-in" style={{ marginTop: 'var(--space-4)' }}>
            <SectionHeader icon={<Icon3DRobot size={22} />} title="AI Summary" subtitle="AI-Generated analysis of the dataset" />
            <div className="ai-summary" style={{ textAlign: 'center' }}>
              <div className="ai-summary__item" style={{ justifyContent: 'flex-start', textAlign: 'left' }}>
                <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}>
                  <svg width="16" height="16" viewBox="0 0 48 48" style={icon3dStyle} fill="none">
                    <defs><linearGradient id="bs1" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#00FF88"/></linearGradient></defs>
                    <circle cx="24" cy="24" r="16" stroke="url(#bs1)" strokeWidth="2" fill="url(#bs1)" fillOpacity=".12" />
                    <circle cx="24" cy="24" r="6" fill="url(#bs1)" opacity=".4" />
                  </svg>
                </span>
                <span><strong>Overall:</strong> The dataset of {result.summary.total_analyzed} reviews shows a {result.summary.positive_pct > 50 ? 'predominantly positive' : 'mixed'} sentiment landscape.</span>
              </div>
              <div className="ai-summary__item" style={{ justifyContent: 'flex-start', textAlign: 'left' }}>
                <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}>
                  <svg width="16" height="16" viewBox="0 0 48 48" style={icon3dStyle} fill="none">
                    <defs><linearGradient id="bs2" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#22C55E"/><stop offset="100%" stopColor="#F43F5E"/></linearGradient></defs>
                    <rect x="8" y="8" width="32" height="32" rx="6" stroke="url(#bs2)" strokeWidth="2" fill="url(#bs2)" fillOpacity=".1" />
                    <path d="M16 24h16M24 16v16" stroke="url(#bs2)" strokeWidth="2" strokeLinecap="round" opacity=".6" />
                  </svg>
                </span>
                <span><strong>Distribution:</strong> {result.summary.positive_pct}% positive, {result.summary.negative_pct}% negative, {result.summary.neutral_pct}% neutral.</span>
              </div>
              <div className="ai-summary__item" style={{ justifyContent: 'flex-start', textAlign: 'left' }}>
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
              <div className="ai-summary__item" style={{ justifyContent: 'flex-start', textAlign: 'left' }}>
                <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}>
                  <svg width="16" height="16" viewBox="0 0 48 48" style={icon3dStyle} fill="none">
                    <defs><linearGradient id="bs4" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#A78BFA"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs>
                    <path d="M24 8L40 38H8z" stroke="url(#bs4)" strokeWidth="2" fill="url(#bs4)" fillOpacity=".15" strokeLinejoin="round" />
                  </svg>
                </span>
                <span><strong>Polarity Score:</strong> Mean polarity is {result.results ? (result.results.reduce((s, r) => s + r.polarity, 0) / result.results.length).toFixed(3) : '—'} ({result.summary.positive_pct > 50 ? 'positive' : 'balanced'} overall).</span>
              </div>
              <div className="ai-summary__item" style={{ justifyContent: 'flex-start', textAlign: 'left' }}>
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
              <div className="ai-summary__item" style={{ justifyContent: 'flex-start', textAlign: 'left' }}>
                <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}>
                  <svg width="16" height="16" viewBox="0 0 48 48" style={icon3dStyle} fill="none">
                    <defs><linearGradient id="bs6" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#A78BFA"/><stop offset="100%" stopColor="#F43F5E"/></linearGradient></defs>
                    <path d="M24 4L6 14v12c0 12 8 16 18 18 10-2 18-6 18-18V14L24 4z" stroke="url(#bs6)" strokeWidth="2" fill="url(#bs6)" fillOpacity=".1" />
                    <path d="M24 18v8M24 30v2" stroke="url(#bs6)" strokeWidth="2" strokeLinecap="round" />
                  </svg>
                </span>
                <span><strong>Sarcasm:</strong> {result.summary.sarcasm_count} reviews ({result.summary.total_analyzed > 0 ? ((result.summary.sarcasm_count / result.summary.total_analyzed) * 100).toFixed(1) : 0}%) flagged as sarcastic.</span>
              </div>
              <div className="ai-summary__item" style={{ justifyContent: 'flex-start', textAlign: 'left' }}>
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
                        generateUniversalJSON({
                          rows: result.results,
                          summary: result.summary,
                          mode: 'bulk',
                          filename: `reviewsense-bulk-${jobId ?? 'export'}.json`,
                          absaAspects: runAbsa ? topAbsaAspects : undefined,
                          sarcasmEnabled: runSarcasm,
                        })
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
