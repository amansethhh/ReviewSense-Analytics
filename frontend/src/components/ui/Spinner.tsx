/**
 * Spinner — Multi-variant loading indicator.
 *   default:  classic rotating ring (existing)
 *   neural:   liquid-fill progress bar with shimmer
 *   orbital:  three rotating rings + pulsing core
 */

interface SpinnerProps {
  size?: number
  variant?: 'default' | 'neural' | 'orbital'
  text?: string
}

export function Spinner({
  size = 24,
  variant = 'default',
  text,
}: SpinnerProps) {
  /* ── Neural liquid-fill loader ─────────────── */
  if (variant === 'neural') {
    return (
      <div className="neural-loader" role="status" aria-label={text ?? 'Loading'}>
        <div className="neural-loader__text">
          {text ?? 'Loading'}
          <span className="neural-loader__dot">.</span>
          <span className="neural-loader__dot">.</span>
          <span className="neural-loader__dot">.</span>
        </div>
        <div className="neural-loader__track">
          <div className="neural-loader__fill" />
        </div>
      </div>
    )
  }

  /* ── Orbital analysis loader ───────────────── */
  if (variant === 'orbital') {
    return (
      <div className="orbital-loader" role="status" aria-label={text ?? 'Analyzing'}>
        <div className="orbital-loader__rings">
          <div className="orbital-loader__ring orbital-loader__ring--outer" />
          <div className="orbital-loader__ring orbital-loader__ring--mid" />
          <div className="orbital-loader__ring orbital-loader__ring--inner" />
          <div className="orbital-loader__core" />
        </div>
        {text && (
          <div className="orbital-loader__text">
            {text}
            <span className="neural-loader__dot">.</span>
            <span className="neural-loader__dot">.</span>
            <span className="neural-loader__dot">.</span>
          </div>
        )}
      </div>
    )
  }

  /* ── Default rotating ring ─────────────────── */
  return (
    <svg
      className="spinner"
      width={size} height={size}
      viewBox="0 0 24 24"
      fill="none"
      aria-label="Loading"
      role="status"
    >
      <circle
        cx="12" cy="12" r="10"
        stroke="currentColor"
        strokeWidth="3"
        strokeDasharray="40 20"
        strokeLinecap="round"
      />
    </svg>
  )
}
