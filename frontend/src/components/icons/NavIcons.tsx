/**
 * ReviewSense — Neural Dark SVG Icon Library
 * Heroicons-style, 24×24 viewBox, stroke-based.
 */

interface IconProps {
  className?: string
  size?: number
}

export function HomeIcon({ className, size = 24 }: IconProps) {
  return (
    <svg className={className} width={size} height={size}
         viewBox="0 0 24 24" fill="none" stroke="currentColor"
         strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
         aria-hidden="true">
      <path d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
    </svg>
  )
}

export function PredictIcon({ className, size = 24 }: IconProps) {
  return (
    <svg className={className} width={size} height={size}
         viewBox="0 0 24 24" fill="none" stroke="currentColor"
         strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
         aria-hidden="true">
      <path d="M13 10V3L4 14h7v7l9-11h-7z" />
    </svg>
  )
}

export function BulkIcon({ className, size = 24 }: IconProps) {
  return (
    <svg className={className} width={size} height={size}
         viewBox="0 0 24 24" fill="none" stroke="currentColor"
         strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
         aria-hidden="true">
      <path d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z" />
    </svg>
  )
}

export function DashboardIcon({ className, size = 24 }: IconProps) {
  return (
    <svg className={className} width={size} height={size}
         viewBox="0 0 24 24" fill="none" stroke="currentColor"
         strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
         aria-hidden="true">
      <path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  )
}

export function LanguageIcon({ className, size = 24 }: IconProps) {
  return (
    <svg className={className} width={size} height={size}
         viewBox="0 0 24 24" fill="none" stroke="currentColor"
         strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
         aria-hidden="true">
      <path d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129" />
    </svg>
  )
}

export function SparkleIcon({ className, size = 24 }: IconProps) {
  return (
    <svg className={className} width={size} height={size}
         viewBox="0 0 24 24" fill="currentColor"
         aria-hidden="true">
      <path d="M14.187 8.096L15 5.25l.813 2.846a4.5 4.5 0 002.09 2.09L20.75 11l-2.846.813a4.5 4.5 0 00-2.09 2.09L15 16.75l-.813-2.846a4.5 4.5 0 00-2.09-2.09L9.25 11l2.846-.813a4.5 4.5 0 002.09-2.09zM7.5 3l.585 2.055a3 3 0 001.36 1.36L11.5 7l-2.055.585a3 3 0 00-1.36 1.36L7.5 11l-.585-2.055a3 3 0 00-1.36-1.36L3.5 7l2.055-.585a3 3 0 001.36-1.36L7.5 3zM8 16.5l.39 1.37a2 2 0 00.91.91L10.67 19.17l-1.37.39a2 2 0 00-.91.91L8 21.84l-.39-1.37a2 2 0 00-.91-.91L5.33 19.17l1.37-.39a2 2 0 00.91-.91L8 16.5z" />
    </svg>
  )
}

export function WarningIcon({ className, size = 24 }: IconProps) {
  return (
    <svg className={className} width={size} height={size}
         viewBox="0 0 24 24" fill="none" stroke="currentColor"
         strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
         aria-hidden="true">
      <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
    </svg>
  )
}

export function SearchIcon({ className, size = 24 }: IconProps) {
  return (
    <svg className={className} width={size} height={size}
         viewBox="0 0 24 24" fill="none" stroke="currentColor"
         strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
         aria-hidden="true">
      <circle cx="11" cy="11" r="8" />
      <path d="M21 21l-4.35-4.35" />
    </svg>
  )
}

export function RocketIcon({ className, size = 24 }: IconProps) {
  return (
    <svg className={className} width={size} height={size}
         viewBox="0 0 24 24" fill="none" stroke="currentColor"
         strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"
         aria-hidden="true">
      <path d="M4.5 16.5c-1.5 1.26-2 5-2 5s3.74-.5 5-2c.71-.84.7-2.13-.09-2.91a2.18 2.18 0 00-2.91-.09zM12 15l-3-3a22 22 0 012-3.95A12.88 12.88 0 0122 2c0 2.72-.78 7.5-6 11a22.35 22.35 0 01-4 2z" />
      <path d="M9 12H4s.55-3.03 2-4c1.62-1.08 5 0 5 0M12 15v5s3.03-.55 4-2c1.08-1.62 0-5 0-5" />
    </svg>
  )
}
