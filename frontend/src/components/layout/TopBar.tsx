import { MobileNav } from './MobileNav'

interface TopBarProps {
  title:    string
  subtitle?: string
}

export function TopBar({ title, subtitle }: TopBarProps) {
  return (
    <header className="topbar">
      {/* Hamburger — CSS hides this on desktop */}
      <MobileNav />

      <div className="topbar__content">
        <h1 className="topbar__title">{title}</h1>
        {subtitle && (
          <p className="topbar__subtitle">{subtitle}</p>
        )}
      </div>

      <div className="topbar__actions" />
    </header>
  )
}
