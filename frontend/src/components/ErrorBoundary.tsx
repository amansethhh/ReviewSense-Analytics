import React, { Component, ReactNode } from 'react'

interface Props {
  children: ReactNode
  fallback?: ReactNode
  pageName?: string
}

interface State {
  hasError: boolean
  error: Error | null
}

export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props)
    this.state = { hasError: false, error: null }
  }

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, info: React.ErrorInfo): void {
    console.error(
      `[ReviewSense ErrorBoundary] ${this.props.pageName ?? 'Unknown'}:`,
      error,
      info,
    )
  }

  render(): ReactNode {
    if (this.state.hasError) {
      if (this.props.fallback) return this.props.fallback
      return (
        <div style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          height: '100vh',
          background: '#0e1117',
          color: '#cdccca',
          fontFamily: 'var(--font-mono, monospace)',
          gap: '16px',
          padding: '32px',
          textAlign: 'center',
        }}>
          <div style={{
            width: 48, height: 48,
            borderRadius: '50%',
            border: '2px solid #00D9FF',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 24,
            color: '#00D9FF',
          }}>!</div>
          <h2 style={{ color: '#00D9FF', margin: 0, fontSize: 18 }}>
            Something went wrong
          </h2>
          <p style={{ color: '#7a7974', maxWidth: 400, lineHeight: 1.6, fontSize: 14 }}>
            {this.props.pageName
              ? `The ${this.props.pageName} page encountered an error.`
              : 'An unexpected error occurred.'}
          </p>
          <p style={{ color: '#5a5957', fontSize: 12, fontFamily: 'var(--font-mono, monospace)' }}>
            {this.state.error?.message ?? 'Unknown error'}
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            style={{
              background: 'transparent',
              border: '1px solid #00D9FF',
              color: '#00D9FF',
              padding: '8px 20px',
              borderRadius: 6,
              cursor: 'pointer',
              fontSize: 13,
              transition: 'all 0.2s ease',
            }}
            onMouseOver={e => (e.currentTarget.style.background = 'rgba(0,217,255,0.1)')}
            onMouseOut={e => (e.currentTarget.style.background = 'transparent')}
          >
            Try again
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
