/**
 * AnalysisLayout — SINGLE SOURCE OF TRUTH
 *
 * This is the CANONICAL layout for ALL analysis pages:
 *   • Bulk Analysis
 *   • Live Prediction
 *   • Language (Multilingual) Analysis
 *   • Any future analysis page
 *
 * Grid: 190px | 1fr | 190px  (2 rows)
 *
 * ❌ DO NOT duplicate this layout
 * ❌ DO NOT create variations
 * ❌ DO NOT inline layout styles per page
 */

import { useRef, useEffect, type CSSProperties, type ReactNode } from 'react'
import { CyberCard } from '@/components/ui/CyberCard'
import { CyberLoader } from '@/components/ui/CyberLoader'
import './AnalysisLayout.css'

/* ═══════════════════════════════════════════════════════════
   3D Icon Style (shared across all panels)
   ═══════════════════════════════════════════════════════════ */

export const icon3dStyle: CSSProperties = {
  filter: 'drop-shadow(0 4px 8px rgba(0,217,255,0.35)) drop-shadow(0 1px 2px rgba(0,0,0,0.4))',
  transform: 'perspective(400px) rotateY(-12deg) rotateX(5deg)',
  display: 'inline-block',
  flexShrink: 0,
}

/* ═══════════════════════════════════════════════════════════
   3D Icon Components (canonical set for all panels)
   ═══════════════════════════════════════════════════════════ */

export function Icon3DPulse({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="pls3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#2dd4bf"/></linearGradient></defs>
      <circle cx="24" cy="24" r="18" stroke="url(#pls3d)" strokeWidth="1.5" fill="url(#pls3d)" fillOpacity=".08" />
      <path d="M8 24h8l4-12 4 24 4-12 4 6 4-6h8" stroke="url(#pls3d)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function Icon3DSentimentPie({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="spie3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#22C55E"/><stop offset="100%" stopColor="#F59E0B"/></linearGradient></defs>
      <circle cx="24" cy="24" r="18" stroke="url(#spie3d)" strokeWidth="2" fill="url(#spie3d)" fillOpacity=".08" />
      <path d="M24 6v18l14 10" stroke="url(#spie3d)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M24 24L10 14" stroke="url(#spie3d)" strokeWidth="1.5" strokeLinecap="round" opacity=".5" />
    </svg>
  )
}

export function Icon3DGearPanel({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="gp3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#A78BFA"/><stop offset="100%" stopColor="#818cf8"/></linearGradient></defs>
      <path d="M24 16a8 8 0 100 16 8 8 0 000-16z" stroke="url(#gp3d)" strokeWidth="2" fill="url(#gp3d)" fillOpacity=".15" />
      <path d="M24 4v6M24 38v6M4 24h6M38 24h6M9.9 9.9l4.2 4.2M33.9 33.9l4.2 4.2M38.1 9.9l-4.2 4.2M14.1 33.9l-4.2 4.2" stroke="url(#gp3d)" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

/* ═══════════════════════════════════════════════════════════
   PanelBadge — shared panel header with icon + title
   ═══════════════════════════════════════════════════════════ */

export function PanelBadge({ icon, label, bg, border, color }: {
  icon: ReactNode; label: string;
  bg: string; border: string; color: string;
}) {
  return (
    <div
      className="analysis-panel-badge"
      style={{ background: bg, border: `1px solid ${border}` }}
    >
      {icon}
      <span style={{
        fontSize: '10px', fontWeight: 700,
        textTransform: 'uppercase', letterSpacing: '0.08em',
        color,
      }}>{label}</span>
    </div>
  )
}

/* ═══════════════════════════════════════════════════════════
   3D Icons for Phases
   ═══════════════════════════════════════════════════════════ */

export function Icon3DGear({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="p03d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#fde047"/><stop offset="100%" stopColor="#f59e0b"/></linearGradient></defs>
      <circle cx="24" cy="24" r="16" stroke="url(#p03d)" strokeWidth="3" fill="url(#p03d)" fillOpacity=".15" />
      <path d="M24 14v20M14 24h20M17 17l14 14M17 31l14-14" stroke="url(#p03d)" strokeWidth="3" strokeLinecap="round" />
    </svg>
  )
}

export function Icon3DSearch({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="p13d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00d9ff"/><stop offset="100%" stopColor="#0ea5e9"/></linearGradient></defs>
      <circle cx="20" cy="20" r="12" stroke="url(#p13d)" strokeWidth="3" fill="url(#p13d)" fillOpacity=".15" />
      <path d="M29 29l10 10" stroke="url(#p13d)" strokeWidth="4" strokeLinecap="round" />
    </svg>
  )
}

export function Icon3DGlobe({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="p23d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#a78bfa"/><stop offset="100%" stopColor="#7c3aed"/></linearGradient></defs>
      <circle cx="24" cy="24" r="18" stroke="url(#p23d)" strokeWidth="3" fill="url(#p23d)" fillOpacity=".15" />
      <ellipse cx="24" cy="24" rx="8" ry="18" stroke="url(#p23d)" strokeWidth="2" fill="none" opacity=".6" />
      <path d="M6 24h36" stroke="url(#p23d)" strokeWidth="2" opacity=".6" />
    </svg>
  )
}

export function Icon3DBrain({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="p33d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00ff88"/><stop offset="100%" stopColor="#22c55e"/></linearGradient></defs>
      <path d="M24 8C14 8 8 16 8 26c0 10 16 14 16 14s16-4 16-14c0-10-6-18-16-18z" stroke="url(#p33d)" strokeWidth="3" fill="url(#p33d)" fillOpacity=".15" />
      <path d="M24 8v32M14 18h20M12 28h24" stroke="url(#p33d)" strokeWidth="2" opacity=".5" />
    </svg>
  )
}

export function Icon3DCheck({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="p43d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#22c55e"/><stop offset="100%" stopColor="#16a34a"/></linearGradient></defs>
      <circle cx="24" cy="24" r="18" stroke="url(#p43d)" strokeWidth="3" fill="url(#p43d)" fillOpacity=".15" />
      <path d="M16 24l6 6 10-12" stroke="url(#p43d)" strokeWidth="4" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

export function Icon3DTimer({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="tmr3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#FDE047"/><stop offset="100%" stopColor="#F59E0B"/></linearGradient></defs>
      <circle cx="24" cy="26" r="18" stroke="url(#tmr3d)" strokeWidth="2" fill="url(#tmr3d)" fillOpacity=".08" />
      <path d="M24 14v12l8 6" stroke="url(#tmr3d)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M20 4h8" stroke="url(#tmr3d)" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

export const PHASE_CONFIG: Record<string, { label: string; color: string; grad: string; icon: ReactNode }> = {
  init:        { label: 'Initializing',        color: '#fde047', grad: 'linear-gradient(90deg,#fde047,#f59e0b)', icon: <Icon3DTimer size={18} /> },
  detecting:   { label: 'Detecting Languages', color: '#00d9ff', grad: 'linear-gradient(90deg,#00d9ff,#0ea5e9)', icon: <Icon3DSearch size={18} /> },
  translating: { label: 'Translating',         color: '#a78bfa', grad: 'linear-gradient(90deg,#a78bfa,#7c3aed)', icon: <Icon3DGlobe size={18} /> },
  analyzing:   { label: 'Analyzing Sentiment', color: '#00ff88', grad: 'linear-gradient(90deg,#00ff88,#22c55e)', icon: <Icon3DBrain size={18} /> },
  done:        { label: 'Finalizing',          color: '#22c55e', grad: 'linear-gradient(90deg,#22c55e,#16a34a)', icon: <Icon3DCheck size={18} /> },
}

const STEPS = [
  { key: 'detecting',   label: 'Detect',    pct: 15  },
  { key: 'translating', label: 'Translate', pct: 40  },
  { key: 'analyzing',   label: 'Analyze',   pct: 68  },
  { key: 'done',        label: 'Done',      pct: 100 },
]

/* ═══════════════════════════════════════════════════════════
   Prop types for AnalysisLayout
   ═══════════════════════════════════════════════════════════ */

export interface AnalysisLayoutProps {
  /* ── Live Stats (top-left) ── */
  processed: number
  total: number | string
  speed: string
  avgConf: string
  errorCount: number
  progressPct: number

  /* ── Config (bottom-left) ── */
  configRows: Array<[string, string]>

  /* ── Sentiment (top-right) ── */
  hasSentimentData: boolean
  posPct: number
  neuPct: number
  negPct: number
  sentTotal: number | string

  /* ── Pipeline (bottom-right) ── */
  pipelineRows: Array<{ label: string; value: number | string; color: string }>

  /* ── Center ── */
  phase: string | undefined
  elapsed: number
  logs: string[]
  prevLogCount: number
  isFailed?: boolean
  failError?: string
  onCancel?: () => void
  onRetry?: () => void
}

/* ═══════════════════════════════════════════════════════════
   LiveStatsCard
   ═══════════════════════════════════════════════════════════ */

export function LiveStatsCard({ processed, total, speed, avgConf, errorCount, progressPct }: {
  processed: number; total: number | string; speed: string;
  avgConf: string; errorCount: number; progressPct: number;
}) {
  const stats = [
    { label: 'Processed', value: `${processed} / ${total || '?'}`, color: 'var(--color-primary-bright)' },
    { label: 'Speed', value: `${speed} r/s`, color: '#2dd4bf' },
    { label: 'Avg Conf', value: avgConf === '—' ? '—' : `${avgConf}%`, color: '#a78bfa' },
    { label: 'Errors', value: String(errorCount), color: errorCount > 0 ? 'var(--color-negative)' : 'var(--color-positive)' },
    { label: 'Progress', value: `${progressPct}%`, color: '#fde047' },
  ]
  return (
    <CyberCard className="analysis-card" style={{ gridColumn: 1, gridRow: 1 }}>
      <PanelBadge icon={<Icon3DPulse />} label="Live Stats"
        bg="rgba(0,217,255,0.06)" border="rgba(0,217,255,0.18)" color="#00d9ff" />
      <div className="analysis-card-body">
        {stats.map(s => (
          <div key={s.label} className="analysis-stat-row">
            <span className="analysis-stat-label">{s.label}</span>
            <span className="analysis-stat-value" style={{ color: s.color }}>{s.value}</span>
          </div>
        ))}
      </div>
    </CyberCard>
  )
}

/* ═══════════════════════════════════════════════════════════
   ConfigCard
   ═══════════════════════════════════════════════════════════ */

export function ConfigCard({ rows }: { rows: Array<[string, string]> }) {
  return (
    <CyberCard className="analysis-card" style={{ gridColumn: 1, gridRow: 2, opacity: 0.85 }}>
      <PanelBadge icon={<Icon3DGearPanel />} label="Config"
        bg="rgba(167,139,250,0.06)" border="rgba(167,139,250,0.18)" color="#a78bfa" />
      <div className="analysis-card-body" style={{ fontSize: '11px' }}>
        {rows.map(([k, v]) => (
          <div key={k} className="analysis-config-row">
            <span style={{ color: 'var(--color-text-faint)' }}>{k}</span>
            <span style={{
              fontWeight: 600, fontFamily: 'var(--font-mono)',
              color: v === 'ON' ? 'var(--color-positive)' : v === 'OFF' ? 'var(--color-text-faint)' : 'var(--color-primary-bright)',
            }}>{v}</span>
          </div>
        ))}
      </div>
    </CyberCard>
  )
}

/* ═══════════════════════════════════════════════════════════
   SentimentDonutChart
   ═══════════════════════════════════════════════════════════ */

export function SentimentDonutChart({ hasSentimentData, posPct, neuPct, negPct, sentTotal }: {
  hasSentimentData: boolean; posPct: number; neuPct: number; negPct: number; sentTotal: number | string;
}) {
  return (
    <CyberCard className="analysis-card" style={{ gridColumn: 3, gridRow: 1 }}>
      <PanelBadge icon={<Icon3DSentimentPie />} label="Sentiment"
        bg="rgba(34,197,94,0.06)" border="rgba(34,197,94,0.18)" color="#22c55e" />
      <div className="analysis-card-body" style={{ alignItems: 'center' }}>
        {hasSentimentData ? (
          <>
            <div
              className="analysis-donut"
              style={{
                background: `conic-gradient(
                  #22c55e 0% ${posPct}%,
                  #f59e0b ${posPct}% ${posPct + neuPct}%,
                  #f43f5e ${posPct + neuPct}% 100%
                )`,
              }}
            >
              <div className="analysis-donut__center">{sentTotal}</div>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', width: '100%' }}>
              {[
                { label: 'Positive', pct: posPct, color: '#22c55e' },
                { label: 'Neutral', pct: neuPct, color: '#f59e0b' },
                { label: 'Negative', pct: negPct, color: '#f43f5e' },
              ].map(s => (
                <div key={s.label}>
                  <div className="analysis-sent-row">
                    <span style={{ color: s.color, fontWeight: 600 }}>{s.label}</span>
                    <span style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>{s.pct}%</span>
                  </div>
                  <div className="analysis-sent-bar">
                    <div className="analysis-sent-fill" style={{
                      background: s.color, width: `${s.pct}%`,
                    }} />
                  </div>
                </div>
              ))}
            </div>
          </>
        ) : (
          <div className="analysis-chart-container">
            <div className="analysis-awaiting">
              <div className="analysis-awaiting__ring" style={{ border: '2px dashed rgba(34,197,94,0.3)' }}>
                <div style={{
                  fontSize: '11px', fontWeight: 700, color: 'var(--color-text-faint)',
                  fontFamily: 'var(--font-mono)',
                }}>0</div>
              </div>
              <div className="analysis-awaiting__text">Awaiting data…</div>
            </div>
          </div>
        )}
      </div>
    </CyberCard>
  )
}

/* ═══════════════════════════════════════════════════════════
   PipelineStatsCard
   ═══════════════════════════════════════════════════════════ */

export function PipelineStatsCard({ hasSentimentData, rows }: {
  hasSentimentData: boolean;
  rows: Array<{ label: string; value: number | string; color: string }>;
}) {
  return (
    <CyberCard className="analysis-card" style={{ gridColumn: 3, gridRow: 2, opacity: 0.85 }}>
      <PanelBadge icon={<Icon3DPulse />} label="Pipeline"
        bg="rgba(0,217,255,0.06)" border="rgba(0,217,255,0.18)" color="#00d9ff" />
      <div className="analysis-card-body" style={{ fontSize: '11px' }}>
        {hasSentimentData ? (
          rows.map(s => (
            <div key={s.label} className="analysis-pipeline-row">
              <span style={{ color: 'var(--color-text-faint)' }}>{s.label}</span>
              <span style={{ fontWeight: 600, fontFamily: 'var(--font-mono)', color: s.color, transition: 'all 0.3s ease' }}>{s.value}</span>
            </div>
          ))
        ) : (
          <div className="analysis-chart-container">
            <div className="analysis-awaiting">
              <div className="analysis-awaiting__ring" style={{ border: '2px dashed rgba(0,217,255,0.3)' }}>
                <div style={{
                  fontSize: '11px', fontWeight: 700, color: 'var(--color-text-faint)',
                  fontFamily: 'var(--font-mono)',
                }}>0</div>
              </div>
              <div className="analysis-awaiting__text">Awaiting data…</div>
            </div>
          </div>
        )}
      </div>
    </CyberCard>
  )
}

/* ═══════════════════════════════════════════════════════════
   CircularLoader
   ═══════════════════════════════════════════════════════════ */

export function CircularLoader() {
  return (
    <div className="analysis-loader-wrap">
      <CyberLoader scale={0.85} />
    </div>
  )
}

/* ═══════════════════════════════════════════════════════════
   ProgressStepper (phase box + progress bar + step dots)
   ═══════════════════════════════════════════════════════════ */

export function ProgressStepper({ phase, progressPct }: {
  phase: string | undefined; progressPct: number;
}) {
  const cfg = PHASE_CONFIG[phase ?? 'init'] ?? PHASE_CONFIG.init
  return (
    <div className="analysis-phase-box">
      {/* Icon + label + pct — all centered */}
      <div className="analysis-phase-header">
        <span style={{ display: 'flex', flexShrink: 0 }}>
          {cfg.icon}
        </span>
        <span className="analysis-phase-label" style={{ color: cfg.color }}>
          {cfg.label}
        </span>
        <span className="analysis-phase-pct">{progressPct}%</span>
      </div>

      {/* Progress bar */}
      <div className="analysis-progress-track">
        <div
          className="analysis-progress-fill"
          style={{
            background: cfg.grad,
            width: `${progressPct}%`,
            boxShadow: `0 0 6px ${cfg.color}55`,
          }}
        />
      </div>

      {/* Step dots */}
      <div className="analysis-steps">
        {STEPS.map(step => {
          const stepDone   = progressPct >= step.pct
          const stepActive = phase === step.key
          return (
            <div key={step.key} className="analysis-step">
              <div
                className="analysis-step__dot"
                style={{
                  background: stepDone ? '#00ff88' : 'rgba(255,255,255,0.12)',
                  boxShadow: stepActive ? '0 0 8px #00ff88' : 'none',
                }}
              />
              <span
                className="analysis-step__label"
                style={{ color: stepDone ? 'var(--color-text-muted)' : 'var(--color-text-faint)' }}
              >{step.label}</span>
            </div>
          )
        })}
      </div>
    </div>
  )
}

/* ═══════════════════════════════════════════════════════════
   AnalysisStatusBar
   ═══════════════════════════════════════════════════════════ */

export function AnalysisStatusBar({ isFailed, processed, total, elapsed }: {
  isFailed?: boolean; processed: number; total: number | string; elapsed: number;
}) {
  return (
    <div className="analysis-status-pill">
      <span className="analysis-status-pill__label">
        {isFailed ? 'Analysis Failed' : 'Analyzing Reviews'}
      </span>
      <span className="analysis-status-pill__meta">
        {processed}/{total || '?'} • {Math.floor(elapsed / 60)}m {elapsed % 60}s
      </span>
    </div>
  )
}

/* ═══════════════════════════════════════════════════════════
   TerminalLog
   ═══════════════════════════════════════════════════════════ */

export function TerminalLog({ logs, prevLogCount }: {
  logs: string[]; prevLogCount: number;
}) {
  const terminalRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight
    }
  }, [logs.length])

  return (
    <div className="analysis-terminal">
      <div className="analysis-terminal__titlebar">
        <span className="analysis-terminal__dot analysis-terminal__dot--red" />
        <span className="analysis-terminal__dot analysis-terminal__dot--yellow" />
        <span className="analysis-terminal__dot analysis-terminal__dot--green" />
        <span className="analysis-terminal__title">ANALYSIS TERMINAL</span>
      </div>
      <div ref={terminalRef} className="analysis-terminal__body">
        {logs.map((log, i) => (
          <div
            key={i}
            className="analysis-terminal__line"
            style={{
              color: i >= prevLogCount ? 'var(--color-text)' : 'var(--color-text-faint)',
              opacity: i >= prevLogCount ? 1 : 0.7,
              animation: i >= prevLogCount ? 'logFadeIn 200ms ease forwards' : 'none',
            }}
          >
            <span className="analysis-terminal__prompt">❯</span>
            {log}
          </div>
        ))}
        {logs.length === 0 && (
          <div style={{ color: 'var(--color-text-faint)' }}>
            <span className="analysis-terminal__prompt">❯</span>
            Initializing analysis pipeline...
          </div>
        )}
      </div>
    </div>
  )
}

/* ═══════════════════════════════════════════════════════════
   AnalysisLayout — THE MASTER COMPONENT
   Assembles all sub-components into the canonical grid.
   ═══════════════════════════════════════════════════════════ */

export function AnalysisLayout(props: AnalysisLayoutProps) {
  const {
    processed, total, speed, avgConf, errorCount, progressPct,
    configRows,
    hasSentimentData, posPct, neuPct, negPct, sentTotal,
    pipelineRows,
    phase, elapsed, logs, prevLogCount,
    isFailed, failError, onCancel, onRetry,
  } = props

  return (
    <div className="card animate-in" style={{ padding: '16px' }}>
      <div className="analysis-grid">

        {/* ── TOP-LEFT: Live Stats ── */}
        <LiveStatsCard
          processed={processed} total={total} speed={speed}
          avgConf={avgConf} errorCount={errorCount} progressPct={progressPct}
        />

        {/* ── TOP-RIGHT: Sentiment ── */}
        <SentimentDonutChart
          hasSentimentData={hasSentimentData}
          posPct={posPct} neuPct={neuPct} negPct={negPct}
          sentTotal={sentTotal}
        />

        {/* ── BOTTOM-LEFT: Config ── */}
        <ConfigCard rows={configRows} />

        {/* ── BOTTOM-RIGHT: Pipeline ── */}
        <PipelineStatsCard
          hasSentimentData={hasSentimentData}
          rows={pipelineRows}
        />

        {/* ── CENTER: Loader + Progress + Status + Terminal ── */}
        <div className="analysis-grid__center">
          <CircularLoader />
          <ProgressStepper phase={phase} progressPct={progressPct} />
          <AnalysisStatusBar
            isFailed={isFailed}
            processed={processed} total={total} elapsed={elapsed}
          />
          <TerminalLog logs={logs} prevLogCount={prevLogCount} />

          {isFailed && (
            <>
              <p className="error-msg">{failError ?? 'Job failed'}</p>
              {onRetry && <button className="neural-btn" onClick={onRetry}>Retry</button>}
            </>
          )}
          {!isFailed && onCancel && (
            <button
              onClick={onCancel}
              style={{
                background: 'transparent', border: 'none',
                color: 'var(--color-primary-bright)',
                fontSize: '13px', cursor: 'pointer',
                display: 'flex', alignItems: 'center', gap: '6px',
                marginTop: '12px'
              }}
            >
              <span>✕</span> Cancel
            </button>
          )}
        </div>

      </div>
    </div>
  )
}

export default AnalysisLayout
