import type { ReactNode } from 'react'

export type EyebrowVariant =
  | 'sentiment-engine'   // AI-POWERED SENTIMENT ENGINE         #00f5d4 → #00bbf9
  | 'live-analysis'      // AI-POWERED LIVE SENTIMENT ANALYSIS  #3b82f6 → #6366f1
  | 'bulk-dashboard'     // BULK SENTIMENT ANALYSIS DASHBOARD   #f59e0b → #f97316
  | 'model-dashboard'    // MODEL PERFORMANCE INTELLIGENCE      #a855f7 → #7c3aed
  | 'multilingual'       // MULTILINGUAL SENTIMENT INTELLIGENCE #10b981 → #22c55e

interface EyebrowPillProps {
  variant: EyebrowVariant
  children: ReactNode
}

/**
 * Animated gradient-border eyebrow pill.
 *
 * Structure:
 *   .eyebrow-pill-wrap  ← ::before pseudo-element sweeps the gradient
 *     .eyebrow-pill-inner  ← dark background layer, sits above gradient
 *       {children}
 */
export function EyebrowPill({ variant, children }: EyebrowPillProps) {
  return (
    <div style={{ display: 'flex', justifyContent: 'center', marginBottom: 'var(--space-5)' }}>
      <div className={`animate-in eyebrow-pill-wrap eyebrow-pill-wrap--${variant}`}>
        <div className="eyebrow-pill-inner">
          {children}
        </div>
      </div>
    </div>
  )
}
