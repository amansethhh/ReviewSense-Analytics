/**
 * Nav3DIcon — Small 3D-styled compass icon for the sidebar "Navigation" label.
 *
 * Uses CSS transforms + gradients to create a 3D glass effect matching
 * the Neural Dark theme. Pure SVG, no external assets.
 */

interface Props {
  size?: number
  className?: string
}

export function Nav3DIcon({ size = 14, className }: Props) {
  return (
    <span
      className={`nav-3d-icon${className ? ` ${className}` : ''}`}
      aria-hidden="true"
    >
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Compass body */}
        <circle
          cx="12"
          cy="12"
          r="10"
          stroke="url(#nav3d-ring)"
          strokeWidth="1.5"
          fill="none"
        />
        {/* Inner ring */}
        <circle
          cx="12"
          cy="12"
          r="6"
          stroke="url(#nav3d-inner)"
          strokeWidth="1"
          fill="none"
          opacity="0.6"
        />
        {/* Compass needle N */}
        <path
          d="M12 2L14.5 10H9.5L12 2Z"
          fill="url(#nav3d-needle-n)"
        />
        {/* Compass needle S */}
        <path
          d="M12 22L14.5 14H9.5L12 22Z"
          fill="url(#nav3d-needle-s)"
        />
        {/* Center dot */}
        <circle cx="12" cy="12" r="1.5" fill="#00D9FF" />
        <defs>
          <linearGradient id="nav3d-ring" x1="2" y1="2" x2="22" y2="22">
            <stop offset="0%" stopColor="#00D9FF" stopOpacity="0.9" />
            <stop offset="100%" stopColor="#0099FF" stopOpacity="0.5" />
          </linearGradient>
          <linearGradient id="nav3d-inner" x1="6" y1="6" x2="18" y2="18">
            <stop offset="0%" stopColor="#00FF88" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#00D9FF" stopOpacity="0.3" />
          </linearGradient>
          <linearGradient id="nav3d-needle-n" x1="12" y1="2" x2="12" y2="12">
            <stop offset="0%" stopColor="#00D9FF" />
            <stop offset="100%" stopColor="#00FF88" />
          </linearGradient>
          <linearGradient id="nav3d-needle-s" x1="12" y1="12" x2="12" y2="22">
            <stop offset="0%" stopColor="#0099FF" stopOpacity="0.6" />
            <stop offset="100%" stopColor="#00D9FF" stopOpacity="0.3" />
          </linearGradient>
        </defs>
      </svg>
    </span>
  )
}
