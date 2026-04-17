import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useApp } from '@/context/AppContext'
import { useSidebar } from '@/context/SidebarContext'
import { SystemStatus } from '@/components/ui/SystemStatus'
import { NeuralInputWrap } from '@/components/ui/NeuralInputWrap'
import { RSLogo } from '@/components/ui/RSLogo'
import {
  HomeIcon,
  PredictIcon,
  BulkIcon,
  DashboardIcon,
  LanguageIcon,
} from '@/components/icons/NavIcons'
import { useActiveJobs } from '@/hooks/useActiveJobs'

const NAV_ITEMS = [
  { path: '/',          label: 'Home',              Icon: HomeIcon      },
  { path: '/predict',   label: 'Live Prediction',   Icon: PredictIcon   },
  { path: '/bulk',      label: 'Bulk Analysis',     Icon: BulkIcon      },
  { path: '/dashboard', label: 'Model Dashboard',   Icon: DashboardIcon },
  { path: '/language',  label: 'Language Analysis',  Icon: LanguageIcon  },
]

/** Pulsing dot shown in the nav bar when any bulk/language job is running. */
function ActiveJobsDot({ count }: { count: number }) {
  if (count === 0) return null
  const label = `${count} job${count !== 1 ? 's' : ''} running`
  return (
    <>
      {/* Keyframes defined inline to avoid modifying global CSS */}
      <style>{`
        @keyframes rs-active-pulse {
          0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(0, 217, 190, 0.5); }
          50%       { opacity: 0.75; box-shadow: 0 0 0 5px rgba(0, 217, 190, 0); }
        }
      `}</style>
      <span
        id="nav-active-jobs-dot"
        title={label}
        aria-label={label}
        style={{
          display: 'inline-block',
          width: '8px',
          height: '8px',
          borderRadius: '50%',
          background: 'var(--color-primary, #00d9be)',
          animation: 'rs-active-pulse 1.5s ease-in-out infinite',
          flexShrink: 0,
          cursor: 'default',
        }}
      />
    </>
  )
}

export function Sidebar() {
  const { state } = useApp()
  const { collapsed } = useSidebar()
  const [activeModel, setActiveModel] = useState('best')
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.75)
  const [domainFilter, setDomainFilter] = useState('All Domains')

  // Nav bar active-jobs indicator (polls /bulk/active every 3s)
  const activeJobs = useActiveJobs()
  const activeCount = activeJobs.length

  return (
    <aside
      className={`sidebar${collapsed ? ' sidebar--collapsed' : ''}`}
      role="navigation"
      aria-label="Main navigation"
    >
      {/* Logo */}
      <div className="sidebar__logo" style={{ alignItems: 'center' }}>
        <RSLogo size={28} />
        <span className="sidebar__logo-text" style={{ fontSize: '18px', lineHeight: 1, letterSpacing: '-0.04em', fontWeight: 700 }}>
          Review<span>Sense</span>
        </span>
      </div>


      {/* Navigation */}
      <div className="sidebar__section">
        <span
          className="sidebar__section-label"
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '6px',
          }}
        >
          Navigation
          <ActiveJobsDot count={activeCount} />
        </span>
        {NAV_ITEMS.map(item => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === '/'}
            data-label={item.label}
            className={({ isActive }) =>
              `sidebar__link${isActive ? ' sidebar__link--active' : ''}`}
          >
            <item.Icon className="nav-icon" size={18} />
            <span className="sidebar__link-label">{item.label}</span>
            <div className="nav-glow" />
          </NavLink>
        ))}
      </div>


      {/* Model Configuration */}
      <div className="sidebar__config">
        <span className="sidebar__section-label">Model Configuration</span>

        <div>
          <div className="sidebar__config-label">Active Model</div>
          <NeuralInputWrap>
            <select
              className="sidebar__config-select"
              value={activeModel}
              onChange={e => setActiveModel(e.target.value)}
            >
              <option value="best">Best</option>
              <option value="linearsvc">Linear SVC</option>
              <option value="lr">Logistic Regression</option>
              <option value="nb">Naive Bayes</option>
              <option value="rf">Random Forest</option>
            </select>
          </NeuralInputWrap>
        </div>

        <div>
          <div className="sidebar__config-label" style={{ justifyContent: 'center', textAlign: 'center', display: 'block' }}>
            Confidence Threshold
          </div>
          <div className="conf-radio">
            <label className="conf-radio__label">
              <input
                type="radio" name="conf" className="conf-radio__input"
                checked={confidenceThreshold === 0.60}
                onChange={() => setConfidenceThreshold(0.60)}
              />
              <span className="conf-radio__name">Low</span>
              <span className="conf-radio__val">0.60</span>
            </label>
            <label className="conf-radio__label">
              <input
                type="radio" name="conf" className="conf-radio__input"
                checked={confidenceThreshold === 0.75}
                onChange={() => setConfidenceThreshold(0.75)}
              />
              <span className="conf-radio__name">Mid</span>
              <span className="conf-radio__val">0.75</span>
            </label>
            <label className="conf-radio__label">
              <input
                type="radio" name="conf" className="conf-radio__input"
                checked={confidenceThreshold === 0.85}
                onChange={() => setConfidenceThreshold(0.85)}
              />
              <span className="conf-radio__name">High</span>
              <span className="conf-radio__val">0.85</span>
            </label>
            <label className="conf-radio__label">
              <input
                type="radio" name="conf" className="conf-radio__input"
                checked={confidenceThreshold === 0.95}
                onChange={() => setConfidenceThreshold(0.95)}
              />
              <span className="conf-radio__name">Max</span>
              <span className="conf-radio__val">0.95</span>
            </label>
            <span className="conf-radio__selection" aria-hidden="true" />
          </div>
        </div>

        <div>
          <div className="sidebar__config-label">Domain Filter</div>
          <NeuralInputWrap>
            <select
              className="sidebar__config-select"
              value={domainFilter}
              onChange={e => setDomainFilter(e.target.value)}
            >
              <option>All Domains</option>
              <option>Electronics</option>
              <option>Food &amp; Beverage</option>
              <option>Hospitality</option>
              <option>E-commerce</option>
            </select>
          </NeuralInputWrap>
        </div>
      </div>

      {/* Footer with System Status */}
      <div className="sidebar__footer">
        <SystemStatus online={state.apiConnected} />
        <div style={{ marginTop: '8px' }}>
          <div>ReviewSense v11.0.0</div>
          <div>&copy; 2026 ReviewSense Analytics</div>
        </div>
      </div>
    </aside>
  )
}
