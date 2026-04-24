/**
 * SidebarProgressLoader — Replaces "NAVIGATION" label during bulk analysis.
 *
 * Shows all 5 pipeline stages (INIT → DETC → TRAN → ANLY → DONE)
 * with their 3D icons matching the Analysis page. Displays real-time
 * OVERALL pipeline progress (not just analyzing stage).
 *
 * Progress uses the backend's `progress` field which tracks the full
 * pipeline: init 0%, detecting 0-15%, translating 15-40%, analyzing 42-100%.
 */
import {
  Icon3DGear,
  Icon3DSearch,
  Icon3DGlobe,
  Icon3DBrain,
  Icon3DCheck,
} from '@/components/layout/AnalysisLayout'
import type { ActiveJob } from '@/api/api'

interface Props {
  jobs: ActiveJob[]
}

/** 5 pipeline stages with short labels for sidebar */
const SIDEBAR_PHASES = [
  { key: 'init',        label: 'INIT', Icon: Icon3DGear,   color: '#fde047' },
  { key: 'detecting',   label: 'DETC', Icon: Icon3DSearch, color: '#00d9ff' },
  { key: 'translating', label: 'TRAN', Icon: Icon3DGlobe,  color: '#a78bfa' },
  { key: 'analyzing',   label: 'ANLY', Icon: Icon3DBrain,  color: '#00ff88' },
  { key: 'done',        label: 'DONE', Icon: Icon3DCheck,  color: '#22c55e' },
] as const

/** Map phase key → index for "active" determination */
const PHASE_ORDER: Record<string, number> = {}
SIDEBAR_PHASES.forEach((p, i) => { PHASE_ORDER[p.key] = i })

export function SidebarProgressLoader({ jobs }: Props) {
  // Use backend's overall pipeline progress (0-100%)
  // Weighted average across all jobs by total rows
  const totalItems = jobs.reduce((sum, j) => sum + j.total, 0)
  const weightedProgress = totalItems > 0
    ? jobs.reduce((sum, j) => sum + (j.progress ?? 0) * j.total, 0) / totalItems
    : 0
  const pct = Math.round(weightedProgress)

  // Determine the "most advanced" phase across all jobs
  let currentPhaseIdx = 0
  for (const job of jobs) {
    const idx = PHASE_ORDER[job.phase] ?? 0
    if (idx > currentPhaseIdx) currentPhaseIdx = idx
  }

  return (
    <div className="sidebar-progress">
      {/* Pipeline steps row — equal width grid */}
      <div className="sidebar-progress__steps">
        {SIDEBAR_PHASES.map((phase, i) => {
          const isDone = i < currentPhaseIdx
          const isActive = i === currentPhaseIdx
          return (
            <div
              key={phase.key}
              className={`sidebar-progress__step${isDone ? ' sidebar-progress__step--done' : ''}${isActive ? ' sidebar-progress__step--active' : ''}`}
            >
              <phase.Icon size={11} />
              <span
                className="sidebar-progress__step-label"
                style={{ color: isDone || isActive ? phase.color : undefined }}
              >
                {phase.label}
              </span>
            </div>
          )
        })}
      </div>

      {/* Progress bar — overall pipeline progress */}
      <div className="sidebar-progress__container">
        <div
          className="sidebar-progress__bar"
          style={{ width: `${pct}%` }}
        />
        <div className="sidebar-progress__text">{pct}%</div>
        <div className="sidebar-progress__particles">
          <span className="sidebar-progress__particle" />
          <span className="sidebar-progress__particle" />
          <span className="sidebar-progress__particle" />
          <span className="sidebar-progress__particle" />
          <span className="sidebar-progress__particle" />
        </div>
      </div>
    </div>
  )
}
