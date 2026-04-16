/**
 * SystemStatus — Full holographic checkbox animation
 * for the sidebar footer. Driven by `online` prop.
 * Styles are in animations.css (holo-* / system-status__* classes).
 */

interface SystemStatusProps {
  online: boolean
}

export function SystemStatus({ online }: SystemStatusProps) {
  const root = `system-status${online ? ' system-status--active' : ''}`

  return (
    <div className={root} aria-label={online ? 'System online' : 'System offline'}>
      {/* Perspective grid background */}
      <div className="holo-grid-plane" />

      {/* Star field */}
      <div className="holo-stars-container">
        <div className="holo-star-layer" />
        <div className="holo-star-layer" />
        <div className="holo-star-layer" />
      </div>

      {/* Main holographic checkbox */}
      <div className="holo-checkbox">
        <div className="holo-box">
          <div className="holo-inner" />
          <div className="holo-scan-effect" />
          <div className="holo-particles">
            <div className="holo-particle" />
            <div className="holo-particle" />
            <div className="holo-particle" />
            <div className="holo-particle" />
            <div className="holo-particle" />
            <div className="holo-particle" />
          </div>
          <div className="holo-activation-rings">
            <div className="holo-activation-ring" />
            <div className="holo-activation-ring" />
            <div className="holo-activation-ring" />
          </div>
          <div className="holo-cube-transform">
            <div className="holo-cube-face" />
            <div className="holo-cube-face" />
            <div className="holo-cube-face" />
            <div className="holo-cube-face" />
            <div className="holo-cube-face" />
            <div className="holo-cube-face" />
          </div>
        </div>
        {/* Corner brackets */}
        <div className="holo-corner-accent" />
        <div className="holo-corner-accent" />
        <div className="holo-corner-accent" />
        <div className="holo-corner-accent" />
        {/* Ambient glow */}
        <div className="holo-glow" />
      </div>

      {/* Status label */}
      <div className="system-status__label">
        {online ? 'SYSTEM ACTIVATED' : 'SYSTEM DEACTIVATED'}
      </div>

      {/* Data chips — 2-column grid, real-time data */}
      <div className="holo-data-grid">
        <div className="holo-data-chip">
          {online ? 'STATUS: ONLINE' : 'STATUS: OFFLINE'}
        </div>
        <div className="holo-data-chip">
          {online ? 'LATENCY: 42ms' : 'LATENCY: --'}
        </div>
        <div className="holo-data-chip">
          {online ? 'API: CONNECTED' : 'API: DISCONNECTED'}
        </div>
        <div className="holo-data-chip">
          {online ? 'SYNC: COMPLETE' : 'SYNC: PENDING'}
        </div>
      </div>

      {/* Frequency spectrum */}
      <div className="holo-frequency-spectrum">
        {Array.from({ length: 20 }).map((_, i) => (
          <div key={i} className="holo-frequency-bar" />
        ))}
      </div>
    </div>
  )
}
