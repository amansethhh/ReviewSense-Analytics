interface ProgressBarProps {
  value:  number   // 0–100
  label?: string
  color?: string
}

export function ProgressBar({
  value, label, color,
}: ProgressBarProps) {
  const clamped = Math.min(100, Math.max(0, value))
  return (
    <div className="progress-wrap"
         role="progressbar"
         aria-valuenow={clamped}
         aria-valuemin={0}
         aria-valuemax={100}>
      {label && (
        <div className="progress-label">
          <span>{label}</span>
          <span>{clamped.toFixed(0)}%</span>
        </div>
      )}
      <div className="progress-track">
        <div
          className="progress-fill"
          style={{
            width:      `${clamped}%`,
            background: color ?? 'var(--color-primary)',
          }}
        />
      </div>
    </div>
  )
}
