import { type ButtonHTMLAttributes, type ReactNode } from 'react'

export type NeuralIconType =
  | 'sparkle'   // AI / Analyze
  | 'download'  // Export / CSV / JSON
  | 'arrow'     // Navigate / Get Started
  | 'dashboard' // View Dashboard
  | 'clear'     // Clear / Reset
  | 'cancel'    // Cancel
  | 'retry'     // Retry
  | 'upload'    // Upload
  | 'toggle'    // Show All / Show Less
  | 'file'      // PDF / Excel / File
  | 'none'      // No icon

interface NeuralButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'gradient'
  size?: 'sm' | 'md' | 'lg'
  icon?: NeuralIconType
  children: ReactNode
}

/* ── Icon Components ── */
const SparkleIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" className="neural-btn__sparkle">
    <path className="neural-btn__spark-path" strokeLinejoin="round" strokeLinecap="round" stroke="currentColor" fill="currentColor" d="M14.187 8.096L15 5.25L15.813 8.096C16.0231 8.83114 16.4171 9.50062 16.9577 10.0413C17.4984 10.5819 18.1679 10.9759 18.903 11.186L21.75 12L18.904 12.813C18.1689 13.0231 17.4994 13.4171 16.9587 13.9577C16.4181 14.4984 16.0241 15.1679 15.814 15.903L15 18.75L14.187 15.904C13.9769 15.1689 13.5829 14.4994 13.0423 13.9587C12.5016 13.4181 11.8321 13.0241 11.097 12.814L8.25 12L11.096 11.187C11.8311 10.9769 12.5006 10.5829 13.0413 10.0423C13.5819 9.50162 13.9759 8.83214 14.186 8.097L14.187 8.096Z" />
    <path className="neural-btn__spark-path" strokeLinejoin="round" strokeLinecap="round" stroke="currentColor" fill="currentColor" d="M6 14.25L5.741 15.285C5.59267 15.8785 5.28579 16.4206 4.85319 16.8532C4.42059 17.2858 3.87853 17.5927 3.285 17.741L2.25 18L3.285 18.259C3.87853 18.4073 4.42059 18.7142 4.85319 19.1468C5.28579 19.5794 5.59267 20.1215 5.741 20.715L6 21.75L6.259 20.715C6.40725 20.1216 6.71398 19.5796 7.14639 19.147C7.5788 18.7144 8.12065 18.4075 8.714 18.259L9.75 18L8.714 17.741C8.12065 17.5925 7.5788 17.2856 7.14639 16.853C6.71398 16.4204 6.40725 15.8784 6.259 15.285L6 14.25Z" />
    <path className="neural-btn__spark-path" strokeLinejoin="round" strokeLinecap="round" stroke="currentColor" fill="currentColor" d="M6.5 4L6.303 4.5915C6.24777 4.75718 6.15472 4.90774 6.03123 5.03123C5.90774 5.15472 5.75718 5.24777 5.5915 5.303L5 5.5L5.5915 5.697C5.75718 5.75223 5.90774 5.84528 6.03123 5.96877C6.15472 6.09226 6.24777 6.24282 6.303 6.4085L6.5 7L6.697 6.4085C6.75223 6.24282 6.84528 6.09226 6.96877 5.96877C7.09226 5.84528 7.24282 5.75223 7.4085 5.697L8 5.5L7.4085 5.303C7.24282 5.24777 7.09226 5.15472 6.96877 5.03123C6.84528 4.90774 6.75223 4.75718 6.697 4.5915L6.5 4Z" />
  </svg>
)

const DownloadIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="neural-btn__icon">
    <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" /><polyline points="7 10 12 15 17 10" /><line x1="12" y1="15" x2="12" y2="3" />
  </svg>
)

const ArrowIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="neural-btn__icon">
    <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
  </svg>
)

const DashboardIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="neural-btn__icon">
    <rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" />
  </svg>
)

const ClearIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="neural-btn__icon">
    <polyline points="1 4 1 10 7 10" /><path d="M3.51 15a9 9 0 102.13-9.36L1 10" />
  </svg>
)

const CancelIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="neural-btn__icon">
    <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
  </svg>
)

const RetryIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="neural-btn__icon">
    <polyline points="23 4 23 10 17 10" /><path d="M20.49 15a9 9 0 11-2.12-9.36L23 10" />
  </svg>
)

const UploadIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="neural-btn__icon">
    <polyline points="16 16 12 12 8 16" /><line x1="12" y1="12" x2="12" y2="21" /><path d="M20.39 18.39A5 5 0 0018 9h-1.26A8 8 0 103 16.3" />
  </svg>
)

const ToggleIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="neural-btn__icon">
    <polyline points="6 9 12 15 18 9" />
  </svg>
)

const FileIcon = () => (
  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="neural-btn__icon">
    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" /><polyline points="14 2 14 8 20 8" /><line x1="16" y1="13" x2="8" y2="13" /><line x1="16" y1="17" x2="8" y2="17" />
  </svg>
)

const ICON_MAP: Record<NeuralIconType, (() => JSX.Element) | null> = {
  sparkle: SparkleIcon,
  download: DownloadIcon,
  arrow: ArrowIcon,
  dashboard: DashboardIcon,
  clear: ClearIcon,
  cancel: CancelIcon,
  retry: RetryIcon,
  upload: UploadIcon,
  toggle: ToggleIcon,
  file: FileIcon,
  none: null,
}

// Auto-detect icon from button text
function detectIcon(text: string, variant: string): NeuralIconType {
  const t = text.toLowerCase()
  // Sentiment feedback buttons — emoji already in child text, no extra icon
  if (t.includes('positive') || t.includes('negative') || t.includes('neutral')) return 'none'
  if (t.includes('analyz') || t.includes('detect') || t.includes('translate')) return 'sparkle'
  if (t.includes('csv') || t.includes('json') || t.includes('export')) return 'download'
  if (t.includes('pdf') || t.includes('excel')) return 'file'
  if (t.includes('dashboard') || t.includes('view')) return 'dashboard'
  if (t.includes('get started') || t.includes('→') || t.includes('navigate')) return 'arrow'
  if (t.includes('clear') || t.includes('start over') || t.includes('another')) return 'clear'
  if (t.includes('cancel')) return 'cancel'
  if (t.includes('retry')) return 'retry'
  if (t.includes('upload') || t.includes('change file')) return 'upload'
  if (t.includes('show')) return 'toggle'
  if (variant === 'ghost') return 'none'
  return 'sparkle'
}

function getChildText(children: ReactNode): string {
  if (typeof children === 'string') return children
  if (typeof children === 'number') return String(children)
  if (Array.isArray(children)) return children.map(getChildText).join(' ')
  return ''
}

export function NeuralButton({
  variant = 'primary',
  size = 'md',
  icon,
  children,
  className = '',
  disabled,
  ...rest
}: NeuralButtonProps) {
  const resolvedIcon = icon ?? detectIcon(getChildText(children), variant)
  const IconComponent = ICON_MAP[resolvedIcon]

  const cls = [
    'neural-btn',
    `neural-btn--${variant}`,
    `neural-btn--${size}`,
    disabled ? 'neural-btn--disabled' : '',
    className,
  ].filter(Boolean).join(' ')

  return (
    <button className={cls} disabled={disabled} {...rest}>
      <div className="neural-btn__dots" />
      {IconComponent && <IconComponent />}
      <span className="neural-btn__text">{children}</span>
    </button>
  )
}
