import React from 'react'
import { TopBar } from './TopBar'
import { useApp } from '@/context/AppContext'
import { WarningIcon } from '@/components/icons/NavIcons'

interface PageWrapperProps {
  title:     string
  subtitle?: string
  hideTopBar?: boolean
  children:  React.ReactNode
}

export function PageWrapper({
  title, subtitle, hideTopBar, children,
}: PageWrapperProps) {
  const { state } = useApp()

  return (
    <main className="page-content">
      {!state.apiConnected && (
        <div className="api-warning-banner">
          <WarningIcon className="warning-icon" />
          Cannot reach backend API. Ensure the backend
          is running on port 8000.
        </div>
      )}
      {!hideTopBar && <TopBar title={title} subtitle={subtitle} />}
      <div className="page-body">
        <div className="page-enter">
          {children}
        </div>
      </div>
    </main>
  )
}
