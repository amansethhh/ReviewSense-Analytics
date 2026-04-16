import { useState } from 'react'
import { NavLink } from 'react-router-dom'
import { useApp } from '@/context/AppContext'
import { useSidebar } from '@/context/SidebarContext'
import { SystemStatus } from '@/components/ui/SystemStatus'
import { NeuralInputWrap } from '@/components/ui/NeuralInputWrap'
import {
  HomeIcon,
  PredictIcon,
  BulkIcon,
  DashboardIcon,
  LanguageIcon,
} from '@/components/icons/NavIcons'

const NAV_ITEMS = [
  { path: '/',          label: 'Home',              Icon: HomeIcon      },
  { path: '/predict',   label: 'Live Prediction',   Icon: PredictIcon   },
  { path: '/bulk',      label: 'Bulk Analysis',     Icon: BulkIcon      },
  { path: '/dashboard', label: 'Model Dashboard',   Icon: DashboardIcon },
  { path: '/language',  label: 'Language Analysis',  Icon: LanguageIcon  },
]

export function Sidebar() {
  const { state } = useApp()
  const { collapsed } = useSidebar()
  const [activeModel, setActiveModel] = useState('best')
  const [confidenceThreshold, setConfidenceThreshold] = useState(0.75)
  const [domainFilter, setDomainFilter] = useState('All Domains')

  return (
    <aside
      className={`sidebar${collapsed ? ' sidebar--collapsed' : ''}`}
      role="navigation"
      aria-label="Main navigation"
    >
      {/* Logo */}
      <div className="sidebar__logo">
        <svg width="28" height="28" viewBox="0 0 28 28"
             fill="none" xmlns="http://www.w3.org/2000/svg"
             aria-label="ReviewSense logo">
          <rect width="28" height="28" rx="8" fill="url(#logo-grad)"/>
          <path d="M7 14 C7 10 10 7 14 7 C18 7 21 10 21 14
                   C21 16 20 17.5 18.5 18.5 L21 21 L18 21
                   L16 19 C15.4 19.3 14.7 19.5 14 19.5
                   C10 19.5 7 17 7 14 Z"
                fill="white" opacity="0.9"/>
          <circle cx="11" cy="13.5" r="1.2" fill="#0d1117"/>
          <circle cx="14" cy="13.5" r="1.2" fill="#0d1117"/>
          <circle cx="17" cy="13.5" r="1.2" fill="#0d1117"/>
          <defs>
            <linearGradient id="logo-grad" x1="0" y1="0" x2="28" y2="28">
              <stop offset="0%" stopColor="#006d80"/>
              <stop offset="100%" stopColor="#004d5a"/>
            </linearGradient>
          </defs>
        </svg>
        <span className="sidebar__logo-text">
          Review<span>Sense</span>
        </span>
      </div>

      {/* Navigation */}
      <div className="sidebar__section">
        <span className="sidebar__section-label">Navigation</span>
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
          <div>ReviewSense v1.0.0</div>
          <div>&copy; 2026 ReviewSense Analytics</div>
        </div>
      </div>
    </aside>
  )
}
