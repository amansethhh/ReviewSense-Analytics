import { useState, useEffect } from 'react'
import { NavLink, useLocation } from 'react-router-dom'
import {
  HomeIcon,
  PredictIcon,
  BulkIcon,
  DashboardIcon,
  LanguageIcon,
} from '@/components/icons/NavIcons'

import type { FC } from 'react'

interface NavItem {
  path:  string
  label: string
  Icon:  FC<{ className?: string; size?: number }>
}

const NAV_ITEMS: NavItem[] = [
  { path: '/',          label: 'Home',              Icon: HomeIcon      },
  { path: '/predict',   label: 'Live Prediction',   Icon: PredictIcon   },
  { path: '/bulk',      label: 'Bulk Analysis',     Icon: BulkIcon      },
  { path: '/language',  label: 'Language Analysis',  Icon: LanguageIcon  },
  { path: '/dashboard', label: 'Model Dashboard',   Icon: DashboardIcon },
]

export function MobileNav() {
  const [open, setOpen] = useState(false)
  const location = useLocation()

  // Close drawer on route change
  useEffect(() => {
    setOpen(false)
  }, [location.pathname])

  // Prevent body scroll when drawer is open
  useEffect(() => {
    document.body.style.overflow = open ? 'hidden' : ''
    return () => { document.body.style.overflow = '' }
  }, [open])

  return (
    <>
      {/* Hamburger button — only visible on mobile */}
      <button
        className="mobile-nav-toggle"
        onClick={() => setOpen(prev => !prev)}
        aria-label={open ? 'Close menu' : 'Open menu'}
        aria-expanded={open}
        aria-controls="mobile-drawer"
      >
        {open ? (
          <svg width="22" height="22" viewBox="0 0 24 24"
               fill="none" stroke="currentColor"
               strokeWidth="2" aria-hidden="true">
            <path d="M18 6 6 18M6 6l12 12"/>
          </svg>
        ) : (
          <svg width="22" height="22" viewBox="0 0 24 24"
               fill="none" stroke="currentColor"
               strokeWidth="2" aria-hidden="true">
            <line x1="3" y1="6"  x2="21" y2="6"/>
            <line x1="3" y1="12" x2="21" y2="12"/>
            <line x1="3" y1="18" x2="21" y2="18"/>
          </svg>
        )}
      </button>

      {/* Backdrop */}
      {open && (
        <div
          className="mobile-drawer-backdrop"
          onClick={() => setOpen(false)}
          aria-hidden="true"
        />
      )}

      {/* Drawer */}
      <nav
        id="mobile-drawer"
        className={`mobile-drawer${open
          ? ' mobile-drawer--open' : ''}`}
        aria-label="Mobile navigation"
      >
        <div className="mobile-drawer__header">
          <span className="mobile-drawer__brand">
            ReviewSense
          </span>
          <button
            className="mobile-drawer__close"
            onClick={() => setOpen(false)}
            aria-label="Close menu"
          >
            <svg width="20" height="20" viewBox="0 0 24 24"
                 fill="none" stroke="currentColor"
                 strokeWidth="2" aria-hidden="true">
              <path d="M18 6 6 18M6 6l12 12"/>
            </svg>
          </button>
        </div>

        <div className="mobile-drawer__nav">
          {NAV_ITEMS.map(item => (
            <NavLink
              key={item.path}
              to={item.path}
              end={item.path === '/'}
              className={({ isActive }) =>
                `mobile-drawer__link${isActive
                  ? ' mobile-drawer__link--active' : ''}`
              }
            >
              <item.Icon className="nav-icon" size={20} />
              <span>{item.label}</span>
            </NavLink>
          ))}
        </div>
      </nav>
    </>
  )
}
