import React from 'react'

interface EmptyStateProps {
  icon?:    string
  title:    string
  message:  string
  action?:  React.ReactNode
}

export function EmptyState({
  icon = '—', title, message, action,
}: EmptyStateProps) {
  return (
    <div className="empty-state">
      <div className="empty-state__icon">{icon}</div>
      <h3 className="empty-state__title">{title}</h3>
      <p  className="empty-state__message">{message}</p>
      {action && (
        <div className="empty-state__action">{action}</div>
      )}
    </div>
  )
}
