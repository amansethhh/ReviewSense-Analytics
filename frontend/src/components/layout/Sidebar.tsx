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
import { Nav3DIcon } from '@/components/icons/Nav3DIcon'
import { SidebarProgressLoader } from '@/components/ui/SidebarProgressLoader'
import { useActiveJobs } from '@/hooks/useActiveJobs'

const NAV_ITEMS = [
  { path: '/',          label: 'Home',              Icon: HomeIcon      },
  { path: '/predict',   label: 'Live Prediction',   Icon: PredictIcon   },
  { path: '/bulk',      label: 'Bulk Analysis',     Icon: BulkIcon      },
  { path: '/dashboard', label: 'Model Dashboard',   Icon: DashboardIcon },
  { path: '/language',  label: 'Language Analysis',  Icon: LanguageIcon  },
]



export function Sidebar() {
  const { state, setConfidenceThreshold } = useApp()
  const { collapsed } = useSidebar()
  const [activeModel, setActiveModel] = useState('best')
  const [domainFilter, setDomainFilter] = useState('All Domains')
  const { confidenceThreshold } = state

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
        {activeCount > 0 ? (
          <SidebarProgressLoader jobs={activeJobs} />
        ) : (
          <span
            className="sidebar__section-label"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '6px',
            }}
          >
            <Nav3DIcon size={14} />
            Navigation
          </span>
        )}
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


      {/* Pipeline Configuration */}
      <div className="sidebar__config">
        <span className="sidebar__section-label">Pipeline Configuration</span>

        <div>
          <div className="sidebar__config-label">Active Model</div>
          <NeuralInputWrap>
            <select
              className="sidebar__config-select"
              value={activeModel}
              onChange={e => setActiveModel(e.target.value)}
            >
              <option value="best">Auto (Hybrid Pipeline)</option>
              <option value="linearsvc">Linear SVC (Benchmark)</option>
              <option value="lr">Logistic Regression (Benchmark)</option>
              <option value="nb">Naive Bayes (Benchmark)</option>
              <option value="rf">Random Forest (Benchmark)</option>
            </select>
          </NeuralInputWrap>
          {/* Display-only note */}
          <div style={{
            fontSize: '9px', color: 'var(--color-text-faint, #555)',
            textAlign: 'center', marginTop: '4px', lineHeight: 1.3,
            opacity: 0.7,
          }}>
            Display only — predictions use Hybrid Transformer Pipeline.
          </div>
        </div>

        <div>
          <div className="sidebar__config-label" style={{ justifyContent: 'center', textAlign: 'center', display: 'block' }}>
            Decision Sensitivity
          </div>
          <div className="conf-radio">
            <label className="conf-radio__label">
              <input
                type="radio" name="conf" className="conf-radio__input"
                checked={confidenceThreshold === 0.60}
                onChange={() => setConfidenceThreshold(0.60)}
              />
              <span className="conf-radio__name">Low</span>
              <span className="conf-radio__val">0.04</span>
            </label>
            <label className="conf-radio__label">
              <input
                type="radio" name="conf" className="conf-radio__input"
                checked={confidenceThreshold === 0.75}
                onChange={() => setConfidenceThreshold(0.75)}
              />
              <span className="conf-radio__name">Mid</span>
              <span className="conf-radio__val">0.06</span>
            </label>
            <label className="conf-radio__label">
              <input
                type="radio" name="conf" className="conf-radio__input"
                checked={confidenceThreshold === 0.85}
                onChange={() => setConfidenceThreshold(0.85)}
              />
              <span className="conf-radio__name">High</span>
              <span className="conf-radio__val">0.08</span>
            </label>
            <label className="conf-radio__label">
              <input
                type="radio" name="conf" className="conf-radio__input"
                checked={confidenceThreshold === 0.95}
                onChange={() => setConfidenceThreshold(0.95)}
              />
              <span className="conf-radio__name">Max</span>
              <span className="conf-radio__val">0.10</span>
            </label>
            <span className="conf-radio__selection" aria-hidden="true" />
          </div>
        </div>

        <div>
          <div className="sidebar__config-label">Content Type (Optional)</div>
          <NeuralInputWrap>
            <select
              className="sidebar__config-select"
              value={domainFilter}
              onChange={e => setDomainFilter(e.target.value)}
            >
              <option>All</option>
              <option>Product Review</option>
              <option>Food Review</option>
              <option>Movie Review</option>
              <option>E-commerce Experience</option>
            </select>
          </NeuralInputWrap>
          <div style={{
            fontSize: '9px', color: 'var(--color-text-faint, #555)',
            textAlign: 'center', marginTop: '4px', lineHeight: 1.3,
            opacity: 0.7,
          }}>
            Does not affect sentiment prediction.
          </div>
        </div>
      </div>

      {/* Footer with System Status */}
      <div className="sidebar__footer">
        <SystemStatus online={state.apiConnected} />
        <div style={{ marginTop: '8px' }}>
          <div>ReviewSense v1.0.0</div>
          <div>&copy; 2026 ReviewSense Analytics</div>
        </div>
      </div>
    </aside>
  )
}
