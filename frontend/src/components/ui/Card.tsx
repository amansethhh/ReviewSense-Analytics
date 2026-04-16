import React from 'react'

interface CardProps {
  children:  React.ReactNode
  title?:    string
  className?: string
  padding?:  'sm' | 'md' | 'lg'
}

export function Card({
  children, title, className, padding = 'md',
}: CardProps) {
  return (
    <div className={`card card--pad-${padding}${
      className ? ` ${className}` : ''}`}>
      {title && (
        <h3 className="card__title">{title}</h3>
      )}
      {children}
    </div>
  )
}
