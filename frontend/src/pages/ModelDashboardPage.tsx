import { useState, useEffect, useRef, type CSSProperties } from 'react'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { NeuralButton } from '@/components/ui/NeuralButton'
import { EyebrowPill } from '@/components/ui/EyebrowPill'
import { OrbitalLoader } from '@/components/ui/OrbitalLoader'
import { ModelComparisonChart } from '@/components/charts/ModelComparisonChart'
import { ROCAUCChart } from '@/components/charts/ROCAUCChart'
import { TrainingTimeChart } from '@/components/charts/TrainingTimeChart'
import { FeatureImportanceChart } from '@/components/charts/FeatureImportanceChart'
import { SentimentTrendChart } from '@/components/charts/SentimentTrendChart'
import { useMetrics } from '@/hooks/useMetrics'
import type { ModelMetric } from '@/types/api.types'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from 'recharts'

type SortKey = keyof Pick<ModelMetric,
  'accuracy' | 'macro_f1' | 'weighted_f1' |
  'macro_prec' | 'auc' | 'train_time_s'>

const METRIC_COLS: { key: SortKey; label: string; fmt: (v: number) => string }[] = [
  { key: 'accuracy',     label: 'Accuracy',  fmt: v => `${v.toFixed(2)}%` },
  { key: 'macro_f1',     label: 'Macro F1',  fmt: v => v.toFixed(4) },
  { key: 'macro_prec',   label: 'Precision', fmt: v => v.toFixed(4) },
  { key: 'auc',          label: 'AUC',       fmt: v => v.toFixed(4) },
]

const ROC_COLORS: Record<string, string> = {
  LinearSVC: '#2dd4bf',
  LogisticRegression: '#818cf8',
  NaiveBayes: '#f59e0b',
  RandomForest: '#f43f5e',
}

const tooltipStyle = {
  background: 'rgba(22,27,34,0.95)',
  border: '1px solid rgba(255,255,255,0.08)',
  borderRadius: '10px',
  boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
  fontFamily: 'Geist, monospace',
  fontSize: '12px',
  color: '#e6edf3',
}

/* ── 3D Icon Style ── */
const icon3dStyle: CSSProperties = {
  filter: 'drop-shadow(0 4px 8px rgba(0,217,255,0.35)) drop-shadow(0 1px 2px rgba(0,0,0,0.4))',
  transform: 'perspective(400px) rotateY(-12deg) rotateX(5deg)',
  display: 'inline-block',
  flexShrink: 0,
}

/* ── Section Header Component ── */
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

/* ── 3D Icons ── */
function Icon3DDashboard({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 64 64" style={icon3dStyle} fill="none">
      <defs><linearGradient id="db3d" x1="0" y1="0" x2="64" y2="64"><stop offset="0%" stopColor="#A78BFA"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs>
      <rect x="6" y="6" width="52" height="52" rx="10" stroke="url(#db3d)" strokeWidth="2" fill="url(#db3d)" fillOpacity=".08" />
      <rect x="12" y="12" width="16" height="16" rx="4" fill="url(#db3d)" opacity=".2" />
      <rect x="36" y="12" width="16" height="16" rx="4" fill="url(#db3d)" opacity=".15" />
      <rect x="12" y="36" width="40" height="16" rx="4" fill="url(#db3d)" opacity=".12" />
    </svg>
  )
}

function Icon3DTrophy({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="tro3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#FDE047"/><stop offset="100%" stopColor="#F59E0B"/></linearGradient></defs>
      <path d="M16 8h16v16c0 6-4 10-8 10s-8-4-8-10V8z" stroke="url(#tro3d)" strokeWidth="2" fill="url(#tro3d)" fillOpacity=".15" />
      <path d="M16 14H8c0 6 4 10 8 10M32 14h8c0 6-4 10-8 10" stroke="url(#tro3d)" strokeWidth="2" strokeLinecap="round" />
      <path d="M20 38h8M24 34v4" stroke="url(#tro3d)" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

function Icon3DTable({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="tbl3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#00FF88"/></linearGradient></defs>
      <rect x="6" y="6" width="36" height="36" rx="6" stroke="url(#tbl3d)" strokeWidth="2" fill="url(#tbl3d)" fillOpacity=".08" />
      <path d="M6 18h36M6 30h36M18 6v36M30 6v36" stroke="url(#tbl3d)" strokeWidth="1.5" opacity=".3" />
    </svg>
  )
}

function Icon3DBarChart({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="bar3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#2dd4bf"/><stop offset="100%" stopColor="#818cf8"/></linearGradient></defs>
      <rect x="6" y="28" width="8" height="14" rx="2" fill="url(#bar3d)" opacity=".3" />
      <rect x="20" y="18" width="8" height="24" rx="2" fill="url(#bar3d)" opacity=".5" />
      <rect x="34" y="8" width="8" height="34" rx="2" fill="url(#bar3d)" opacity=".7" />
      <path d="M6 44h36" stroke="url(#bar3d)" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

function Icon3DMatrix({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="mtx3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#F43F5E"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs>
      <rect x="6" y="6" width="16" height="16" rx="3" fill="url(#mtx3d)" opacity=".3" />
      <rect x="26" y="6" width="16" height="16" rx="3" fill="url(#mtx3d)" opacity=".15" />
      <rect x="6" y="26" width="16" height="16" rx="3" fill="url(#mtx3d)" opacity=".15" />
      <rect x="26" y="26" width="16" height="16" rx="3" fill="url(#mtx3d)" opacity=".3" />
    </svg>
  )
}

function Icon3DROC({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="roc3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#818cf8"/><stop offset="100%" stopColor="#2dd4bf"/></linearGradient></defs>
      <path d="M6 42L6 6" stroke="url(#roc3d)" strokeWidth="2" strokeLinecap="round" />
      <path d="M6 42H42" stroke="url(#roc3d)" strokeWidth="2" strokeLinecap="round" />
      <path d="M6 42C10 38 14 28 20 22 26 16 32 12 42 6" stroke="url(#roc3d)" strokeWidth="2.5" strokeLinecap="round" fill="none" />
      <path d="M6 42L42 6" stroke="url(#roc3d)" strokeWidth="1" strokeDasharray="4 4" opacity=".3" />
    </svg>
  )
}

function Icon3DTimer({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="tmr3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#FDE047"/><stop offset="100%" stopColor="#F59E0B"/></linearGradient></defs>
      <circle cx="24" cy="26" r="18" stroke="url(#tmr3d)" strokeWidth="2" fill="url(#tmr3d)" fillOpacity=".08" />
      <path d="M24 14v12l8 6" stroke="url(#tmr3d)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M20 4h8" stroke="url(#tmr3d)" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

function Icon3DFeature({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="ft3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00FF88"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs>
      <rect x="8" y="10" width="32" height="4" rx="2" fill="url(#ft3d)" opacity=".6" />
      <rect x="8" y="18" width="24" height="4" rx="2" fill="url(#ft3d)" opacity=".45" />
      <rect x="8" y="26" width="18" height="4" rx="2" fill="url(#ft3d)" opacity=".35" />
      <rect x="8" y="34" width="12" height="4" rx="2" fill="url(#ft3d)" opacity=".2" />
    </svg>
  )
}

function Icon3DTrend({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="trd3d2" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#00FF88"/></linearGradient></defs>
      <path d="M6 38l10-14 8 6 8-12 10-8" stroke="url(#trd3d2)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" fill="none" />
      <circle cx="42" cy="10" r="3" fill="url(#trd3d2)" />
    </svg>
  )
}

function Icon3DRadar({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="rdr3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#A78BFA"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs>
      <circle cx="24" cy="24" r="18" stroke="url(#rdr3d)" strokeWidth="1.5" fill="none" opacity=".3" />
      <circle cx="24" cy="24" r="12" stroke="url(#rdr3d)" strokeWidth="1.5" fill="none" opacity=".2" />
      <circle cx="24" cy="24" r="6" stroke="url(#rdr3d)" strokeWidth="1.5" fill="none" opacity=".15" />
      <path d="M24 6v36M6 24h36M10 10l28 28M38 10L10 38" stroke="url(#rdr3d)" strokeWidth="1" opacity=".12" />
      <path d="M24 12L34 20 30 34 18 34 14 20Z" stroke="url(#rdr3d)" strokeWidth="2" fill="url(#rdr3d)" fillOpacity=".1" />
    </svg>
  )
}

function Icon3DStar({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="str3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#FDE047"/><stop offset="100%" stopColor="#F59E0B"/></linearGradient></defs>
      <path d="M24 4l6 14h14l-11 9 4 15-13-9-13 9 4-15L4 18h14z" stroke="url(#str3d)" strokeWidth="2" fill="url(#str3d)" fillOpacity=".2" />
    </svg>
  )
}

function Icon3DAlert({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="alt3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#F43F5E"/><stop offset="100%" stopColor="#FB7185"/></linearGradient></defs>
      <path d="M24 6L4 42h40L24 6z" stroke="url(#alt3d)" strokeWidth="2" fill="url(#alt3d)" fillOpacity=".1" strokeLinejoin="round" />
      <path d="M24 20v10M24 34v2" stroke="url(#alt3d)" strokeWidth="2.5" strokeLinecap="round" />
    </svg>
  )
}

function Icon3DBolt({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="blt3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#00FF88"/></linearGradient></defs>
      <path d="M28 4L12 26h12L20 44 36 22H24L28 4z" stroke="url(#blt3d)" strokeWidth="2" fill="url(#blt3d)" fillOpacity=".15" strokeLinejoin="round" />
    </svg>
  )
}


export function ModelDashboardPage() {
  const { data, loading, error } = useMetrics()
  const [sortKey, setSortKey] = useState<SortKey>('accuracy')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc')
  const [ringOffset, setRingOffset] = useState(276.46)
  const ringRef = useRef(false)

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir(d => d === 'desc' ? 'asc' : 'desc')
    else { setSortKey(key); setSortDir('desc') }
  }

  // Animate accuracy ring on mount
  useEffect(() => {
    if (data && !ringRef.current) {
      ringRef.current = true
      const best = data.models.find(m => m.is_best)
      if (best) {
        setTimeout(() => {
          setRingOffset(276.46 * (1 - best.accuracy / 100))
        }, 100)
      }
    }
  }, [data])

  if (loading) return (
    <PageWrapper title="Model Dashboard" subtitle="Performance metrics for all 4 trained classifiers" hideTopBar>
      <div className="card animate-in card--animated" style={{ padding: 'var(--space-4)' }}>
        <OrbitalLoader text="Analyzing Models" />
      </div>
    </PageWrapper>
  )

  if (error || !data) return (
    <PageWrapper title="Model Dashboard" hideTopBar>
      <div className="empty-state">
        <div className="empty-state__icon">!</div>
        <h3 className="empty-state__title">Could not load metrics</h3>
        <p className="empty-state__message">{error ?? 'No data available'}</p>
        <NeuralButton onClick={() => window.location.reload()}>Retry</NeuralButton>
      </div>
    </PageWrapper>
  )

  const sortedModels = [...data.models].sort((a, b) => {
    const av = a[sortKey] as number
    const bv = b[sortKey] as number
    return sortDir === 'desc' ? bv - av : av - bv
  })

  const bestModel = data.models.find(m => m.is_best)

  // Accuracy + Macro F1 grouped bar data
  const groupedBarData = data.models.map(m => ({
    name: m.name,
    Accuracy: m.accuracy,
    'Macro F1': m.macro_f1 * 100,
  }))

  // ROC models
  const rocModels = data.models.map(m => ({
    name: m.name,
    auc: m.auc,
    color: ROC_COLORS[m.name] ?? '#8b949e',
  }))

  return (
    <PageWrapper title="Model Dashboard" subtitle="Performance metrics for all 4 trained classifiers" hideTopBar>

      {/* ── Eyebrow heading ── */}
      <EyebrowPill variant="model-dashboard">
        <Icon3DDashboard size={22} />
        Model Performance Intelligence Dashboard
      </EyebrowPill>

      {/* SECTION 1 — Best Model Banner */}
      {bestModel && (
        <div className="card animate-in">
          <SectionHeader icon={<Icon3DTrophy size={22} />} title={bestModel.name} subtitle="Best performing model across all metrics" />
          <div className="best-model-banner">
            <div>
              <div className="best-model-banner__acc">
                Accuracy: {bestModel.accuracy.toFixed(2)}% · Macro F1: {(bestModel.macro_f1 * 100).toFixed(2)}%
              </div>
              <p className="helper-text" style={{ marginTop: 'var(--space-2)' }}>
                {bestModel.description ?? 'Best performing model across all metrics.'}
              </p>
              <span className="badge badge-info" style={{ marginTop: 'var(--space-2)' }}>
                {bestModel.name}
              </span>
            </div>
            <div className="accuracy-ring">
              <svg width="100" height="100" viewBox="0 0 100 100">
                <circle cx="50" cy="50" r="44" fill="none"
                  stroke="rgba(255,255,255,0.05)" strokeWidth="4" />
                <circle cx="50" cy="50" r="44" fill="none"
                  stroke="var(--color-primary-bright)" strokeWidth="4"
                  strokeLinecap="round"
                  strokeDasharray="276.46"
                  strokeDashoffset={ringOffset}
                  style={{ transition: 'stroke-dashoffset 1.2s cubic-bezier(0.16,1,0.3,1)' }} />
              </svg>
              <div className="accuracy-ring__value">{bestModel.accuracy.toFixed(1)}%</div>
            </div>
          </div>
        </div>
      )}

      {/* SECTION 2 — All Models Leaderboard */}
      <div className="card animate-in animate-in--d1" style={{ marginTop: 'var(--space-4)' }}>
        <SectionHeader icon={<Icon3DTable size={22} />} title="All Models Comparison" subtitle="Click column headers to sort" />
        <div className="results-table-wrap">
          <table className="leaderboard-table">
            <thead><tr>
              <th>Rank</th>
              <th>Model</th>
              {METRIC_COLS.map(c => (
                <th key={c.key} onClick={() => toggleSort(c.key)}>
                  {c.label}{sortKey === c.key ? (sortDir === 'desc' ? ' ↓' : ' ↑') : ''}
                </th>
              ))}
            </tr></thead>
            <tbody>
              {sortedModels.map((model, i) => (
                <tr key={model.name} className={model.is_best ? 'best-row' : ''}>
                  <td>
                    <span className={`rank-badge rank-badge--${Math.min(i + 1, 4)}`}>
                      {i + 1}
                    </span>
                  </td>
                  <td style={{ fontWeight: model.is_best ? 700 : 500 }}>
                    {model.is_best ? '⭐ ' : ''}{model.name}
                  </td>
                  {METRIC_COLS.map(c => (
                    <td key={c.key} className="col-num">
                      {c.fmt(model[c.key] as number)}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* SECTION 3 — Accuracy & Macro F1 Grouped Bar */}
      <div className="card animate-in animate-in--d2" style={{ marginTop: 'var(--space-4)' }}>
        <SectionHeader icon={<Icon3DBarChart size={22} />} title="Accuracy & Macro F1" subtitle="Grouped comparison across models" />
        <div className="card-body">
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={groupedBarData} margin={{ left: 10, right: 30 }}>
              <CartesianGrid stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="name" tick={{ fill: '#8b949e', fontSize: 11 }}
                     axisLine={false} tickLine={false} />
              <YAxis tick={{ fill: '#8b949e', fontSize: 11 }}
                     axisLine={false} tickLine={false}
                     tickFormatter={(v: number) => `${v}%`} />
              <Tooltip contentStyle={tooltipStyle}
                       formatter={(v: number) => [`${v.toFixed(2)}%`, '']} />
              <Legend formatter={(v: string) => (
                <span style={{ color: '#8b949e', fontSize: '12px',
                  fontFamily: 'Geist, monospace' }}>{v}</span>
              )} />
              <Bar dataKey="Accuracy" fill="#2dd4bf" radius={[4,4,0,0]}
                   animationBegin={0} animationDuration={800} />
              <Bar dataKey="Macro F1" fill="#818cf8" radius={[4,4,0,0]}
                   animationBegin={0} animationDuration={800} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* SECTION 4 — Confusion Matrices */}
      <div className="card animate-in animate-in--d3" style={{ marginTop: 'var(--space-4)' }}>
        <SectionHeader icon={<Icon3DMatrix size={22} />} title="Confusion Matrices" subtitle="Prediction accuracy heatmaps per model" />
        <div className="card-body">
          <div className="cm-grid">
            {data.confusion_matrices.map(cm => (
              <div key={cm.model_name} className="cm-matrix card" style={{ padding: 'var(--space-3)' }}>
                <div className="cm-matrix__title">{cm.model_name}</div>
                <div style={{ display: 'grid',
                  gridTemplateColumns: `auto repeat(${cm.labels.length}, 1fr)`,
                  gap: '2px' }}>
                  {/* Header row */}
                  <div className="cm-cell cm-cell--header" />
                  {cm.labels.map(l => (
                    <div key={`h-${l}`} className="cm-cell cm-cell--header">
                      {l.slice(0,3)}
                    </div>
                  ))}
                  {/* Data rows */}
                  {cm.matrix.map((row, ri) => (
                    <span key={ri} style={{ display: 'contents' }}>
                      <div className="cm-cell cm-cell--rowlabel">{cm.labels[ri].slice(0,3)}</div>
                      {row.map((cell, ci) => (
                        <div key={ci}
                          className={`cm-cell ${ri === ci ? 'cm-cell--diagonal' : 'cm-cell--off'}`}>
                          {cell.toLocaleString()}
                        </div>
                      ))}
                    </span>
                  ))}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* SECTION 5 — ROC-AUC Curves */}
      <div className="card animate-in animate-in--d4" style={{ marginTop: 'var(--space-4)' }}>
        <SectionHeader icon={<Icon3DROC size={22} />} title="ROC-AUC Curves" subtitle="Receiver operating characteristic per model" />
        <div className="card-body">
          <ROCAUCChart models={rocModels} />
        </div>
      </div>

      {/* SECTION 6 — Training Time */}
      <div className="card animate-in animate-in--d5" style={{ marginTop: 'var(--space-4)' }}>
        <SectionHeader icon={<Icon3DTimer size={22} />} title="Training Time Comparison" subtitle="Wall-clock time per model" />
        <div className="card-body">
          <TrainingTimeChart />
        </div>
      </div>

      {/* SECTION 7 — Feature Importance */}
      <div className="card animate-in" style={{ marginTop: 'var(--space-4)' }}>
        <SectionHeader icon={<Icon3DFeature size={22} />} title="Global Feature Importance"
          subtitle={`Top 20 most influential features — ${bestModel?.name ?? 'LinearSVC'} model`} />
        <div className="card-body">
          <FeatureImportanceChart />
        </div>
      </div>

      {/* SECTION 8 — Sentiment Trend */}
      <div className="card animate-in" style={{ marginTop: 'var(--space-4)' }}>
        <SectionHeader icon={<Icon3DTrend size={22} />} title="Sentiment Trend"
          subtitle="Simulated monthly sentiment distribution" />
        <div className="card-body">
          <SentimentTrendChart />
        </div>
      </div>

      {/* SECTION 9 — Model Comparison Radar */}
      <div className="card animate-in" style={{ marginTop: 'var(--space-4)' }}>
        <SectionHeader icon={<Icon3DRadar size={22} />} title="Model Performance Radar" subtitle="Multi-dimensional model comparison" />
        <div className="card-body">
          <ModelComparisonChart models={data.models} />
        </div>
      </div>

      {/* SECTION 10 — Model Insights */}
      <div className="model-insights" style={{ marginTop: 'var(--space-4)' }}>
        <div className="card model-insight-card model-insight-card--top animate-in">
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: '8px' }}>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: '10px',
              background: 'rgba(253, 224, 71, 0.06)', border: '1px solid rgba(253, 224, 71, 0.15)',
              borderRadius: '12px', padding: '8px 20px',
            }}>
              <Icon3DStar size={20} />
              <span style={{ fontWeight: 700, fontSize: 'var(--text-sm)' }}>Top Pick</span>
            </div>
            <div className="model-insight-card__text">
              {bestModel?.name ?? 'LinearSVC'} achieves the best balance of accuracy
              and speed. Recommended for production.
            </div>
          </div>
        </div>
        <div className="card model-insight-card model-insight-card--action animate-in animate-in--d1">
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: '8px' }}>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: '10px',
              background: 'rgba(244, 63, 94, 0.06)', border: '1px solid rgba(244, 63, 94, 0.15)',
              borderRadius: '12px', padding: '8px 20px',
            }}>
              <Icon3DAlert size={20} />
              <span style={{ fontWeight: 700, fontSize: 'var(--text-sm)' }}>Action Needed</span>
            </div>
            <div className="model-insight-card__text">
              Random Forest shows lower F1 on neutral class.
              Consider retraining with balanced dataset.
            </div>
          </div>
        </div>
        <div className="card model-insight-card model-insight-card--tip animate-in animate-in--d2">
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: '8px' }}>
            <div style={{
              display: 'inline-flex', alignItems: 'center', gap: '10px',
              background: 'rgba(0, 217, 255, 0.06)', border: '1px solid rgba(0, 217, 255, 0.15)',
              borderRadius: '12px', padding: '8px 20px',
            }}>
              <Icon3DBolt size={20} />
              <span style={{ fontWeight: 700, fontSize: 'var(--text-sm)' }}>Efficiency Tip</span>
            </div>
            <div className="model-insight-card__text">
              Naive Bayes is 15× faster than Random Forest
              with only 6% accuracy trade-off.
            </div>
          </div>
        </div>
      </div>

      {/* SECTION 11 — Translation Pipeline Health (W4-3) */}
      <TranslationDashboard />
    </PageWrapper>
  )
}

/* ── W4-3: Translation Pipeline Health ── */
interface TranslationStats {
  total_translations: number
  method_breakdown: Record<string, number>
  failure_rate_pct: number
  per_language: Record<string, { count: number; failed: number }>
  google_reachable?: boolean
}

function TranslationDashboard() {
  const [stats, setStats] = useState<TranslationStats | null>(null)
  const [loadingT, setLoadingT] = useState(true)

  useEffect(() => {
    fetch('http://localhost:8000/metrics/translations')
      .then(r => r.json())
      .then((d: TranslationStats) => { setStats(d); setLoadingT(false) })
      .catch(() => setLoadingT(false))
  }, [])

  if (loadingT) return null

  // C3: Empty state when no translations
  if (!stats || stats.total_translations === 0) {
    return (
      <div className="card animate-in" style={{ marginTop: 'var(--space-4)' }}>
        <SectionHeader icon={<Icon3DBolt size={22} />} title="Translation Pipeline Health" subtitle="Real-time translation metrics" />
        <div style={{ padding: 'var(--space-6)', textAlign: 'center' }}>
          <div style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)' }}>
            No translations recorded yet. Analyze a non-English review to populate this dashboard.
          </div>
        </div>
      </div>
    )
  }

  const langEntries = Object.entries(stats.per_language)
    .sort(([, a], [, b]) => b.count - a.count)

  return (
    <div className="card animate-in" style={{ marginTop: 'var(--space-4)' }}>
      <SectionHeader icon={<Icon3DBolt size={22} />} title="Translation Pipeline Health" subtitle="Real-time translation metrics" />
      <div style={{ padding: 'var(--space-4)' }}>
        {/* KPI row */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--space-3)' }}>
          <div style={{
            display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px',
            padding: 'var(--space-3)', background: 'rgba(0,217,255,0.06)',
            border: '1px solid rgba(0,217,255,0.15)', borderRadius: '10px',
          }}>
            <div style={{ fontSize: 'var(--text-2xl)', fontWeight: 700, color: 'var(--color-primary-bright)', fontFamily: 'var(--font-mono)' }}>
              {stats.total_translations}
            </div>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Total</div>
          </div>
          <div style={{
            display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px',
            padding: 'var(--space-3)',
            background: stats.failure_rate_pct > 10 ? 'rgba(244,63,94,0.06)' : 'rgba(34,197,94,0.06)',
            border: `1px solid ${stats.failure_rate_pct > 10 ? 'rgba(244,63,94,0.15)' : 'rgba(34,197,94,0.15)'}`,
            borderRadius: '10px',
          }}>
            <div style={{ fontSize: 'var(--text-2xl)', fontWeight: 700, color: stats.failure_rate_pct > 10 ? 'var(--color-negative)' : 'var(--color-positive)', fontFamily: 'var(--font-mono)' }}>
              {stats.failure_rate_pct.toFixed(1)}%
            </div>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Failure Rate</div>
          </div>
          <div style={{
            display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px',
            padding: 'var(--space-3)', background: 'rgba(167,139,250,0.06)',
            border: '1px solid rgba(167,139,250,0.15)', borderRadius: '10px',
          }}>
            <div style={{ fontSize: 'var(--text-2xl)', fontWeight: 700, color: '#a78bfa', fontFamily: 'var(--font-mono)' }}>
              {stats.method_breakdown.helsinki_success ?? 0}
            </div>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Helsinki-NLP</div>
          </div>
          <div style={{
            display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px',
            padding: 'var(--space-3)', background: 'rgba(245,158,11,0.06)',
            border: '1px solid rgba(245,158,11,0.15)', borderRadius: '10px',
          }}>
            <div style={{ fontSize: 'var(--text-2xl)', fontWeight: 700, color: 'var(--color-neutral-sent)', fontFamily: 'var(--font-mono)' }}>
              {stats.method_breakdown.google_success ?? 0}
            </div>
            <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em' }}>Google</div>
          </div>
        </div>

        {/* Google Translate availability badge */}
        <div style={{ display: 'flex', justifyContent: 'center', marginTop: 'var(--space-3)' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            gap: 'var(--space-2)',
            padding: '4px 14px',
            background: stats.google_reachable
              ? 'rgba(34,197,94,0.08)'
              : 'rgba(122,121,116,0.08)',
            border: `1px solid ${stats.google_reachable
              ? 'rgba(34,197,94,0.25)'
              : 'rgba(122,121,116,0.25)'}`,
            borderRadius: '9999px',
            fontSize: 'var(--text-xs)',
            color: stats.google_reachable
              ? 'var(--color-positive)'
              : 'var(--color-text-muted)',
          }}>
            <span style={{
              width: 6, height: 6,
              borderRadius: '50%',
              background: stats.google_reachable ? 'var(--color-positive)' : '#7a7974',
              display: 'inline-block',
            }} />
            Google Translate: {stats.google_reachable ? 'Reachable' : 'Unavailable (Helsinki-NLP active)'}
          </div>
        </div>

        {/* Per-language table */}
        {langEntries.length > 0 && (
          <div style={{ marginTop: 'var(--space-4)' }}>
            <div className="results-table-wrap">
              <table className="leaderboard-table">
                <thead><tr>
                  <th>Language</th>
                  <th>Requests</th>
                  <th>Failed</th>
                  <th>Failure %</th>
                </tr></thead>
                <tbody>
                  {langEntries.map(([lang, info]) => (
                    <tr key={lang}>
                      <td style={{ fontWeight: 600 }}>{lang}</td>
                      <td className="col-num">{info.count}</td>
                      <td className="col-num">{info.failed}</td>
                      <td className="col-num">
                        {info.count > 0 ? (info.failed / info.count * 100).toFixed(1) : '0.0'}%
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
