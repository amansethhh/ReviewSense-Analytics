import { useEffect, useRef } from 'react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AppProvider, useApp } from '@/context/AppContext'
import { SidebarProvider, useSidebar } from '@/context/SidebarContext'
import { Sidebar }     from '@/components/layout/Sidebar'
import { ToastContainer } from '@/components/ui/Toast'
import { getHealth } from '@/api/api'
import { HomePage }            from '@/pages/HomePage'
import { LivePredictionPage }  from '@/pages/LivePredictionPage'
import { BulkAnalysisPage }    from '@/pages/BulkAnalysisPage'
import { LanguageAnalysisPage }
  from '@/pages/LanguageAnalysisPage'
import { ErrorBoundary } from '@/components/ErrorBoundary'
import { ModelDashboardPage }
  from '@/pages/ModelDashboardPage'

function HealthPoller() {
  const { dispatch } = useApp()
  const intervalRef = useRef<ReturnType<typeof setInterval>
    | null>(null)

  useEffect(() => {
    const check = async () => {
      try {
        await getHealth()
        dispatch({ type: 'SET_API_STATUS', payload: true })
      } catch {
        dispatch({ type: 'SET_API_STATUS', payload: false })
      }
    }

    check()
    intervalRef.current = setInterval(check, 30000)
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current)
    }
  }, [dispatch])

  return null
}

function AppContent() {
  const { collapsed, toggle } = useSidebar()

  return (
    <>
      <HealthPoller />
      <BrowserRouter>
        <div className={`app-layout${collapsed ? ' app-layout--collapsed' : ''}`}>
          <Sidebar />

          {/* Toggle button lives OUTSIDE the sidebar to avoid overflow clipping */}
          <button
            className={`sidebar-toggle-btn${collapsed ? ' sidebar-toggle-btn--collapsed' : ''}`}
            onClick={toggle}
            aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
          >
            <span className={`sidebar-toggle-btn__icon${collapsed ? ' sidebar-toggle-btn__icon--flipped' : ''}`}>
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                <path d="M9 2L4 7L9 12"
                  stroke="currentColor" strokeWidth="2"
                  strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </span>
            <span className="sidebar-toggle-btn__ring" aria-hidden="true" />
          </button>

          <div className="main-column">
            <Routes>
              <Route path="/" element={
                <ErrorBoundary pageName="Home"><HomePage /></ErrorBoundary>
              } />
              <Route path="/predict" element={
                <ErrorBoundary pageName="Live Prediction"><LivePredictionPage /></ErrorBoundary>
              } />
              <Route path="/bulk" element={
                <ErrorBoundary pageName="Bulk Analysis"><BulkAnalysisPage /></ErrorBoundary>
              } />
              <Route path="/language" element={
                <ErrorBoundary pageName="Language Analysis"><LanguageAnalysisPage /></ErrorBoundary>
              } />
              <Route path="/dashboard" element={
                <ErrorBoundary pageName="Model Dashboard"><ModelDashboardPage /></ErrorBoundary>
              } />
            </Routes>
          </div>
        </div>
        <ToastContainer />
      </BrowserRouter>
    </>
  )
}

export default function App() {
  return (
    <AppProvider>
      <SidebarProvider>
        <AppContent />
      </SidebarProvider>
    </AppProvider>
  )
}
