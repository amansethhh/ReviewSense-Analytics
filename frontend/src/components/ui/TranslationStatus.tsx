/**
 * TranslationStatus — Badge component for translation quality indicators.
 *
 * V4: NLLB is the ONLY translation engine. All references to
 * Helsinki-NLP, Google Translate, and tiered fallbacks removed.
 */

interface TranslationStatusProps {
  status: string
  polarityInverted?: boolean
  method?: string
  className?: string
}

const STATUS_CONFIG: Record<string, { color: string; text: string; icon: string }> = {
  success:           { color: '#00c851', text: 'NLLB ✓',       icon: '✓' },
  nllb:              { color: '#00c851', text: 'NLLB',         icon: '✓' },
  cache:             { color: '#4CAF50', text: 'Cached',       icon: '✓' },
  passthrough:       { color: '#888',    text: 'English',      icon: '—' },
  failed:            { color: '#ff4b4b', text: 'Failed',       icon: '✗' },
  passthrough_failed:{ color: '#ff4b4b', text: 'Fallback',     icon: '✗' },
  failed_raw_predict:{ color: '#ff4b4b', text: 'Raw Predict',  icon: '✗' },
  timeout:           { color: '#ff4b4b', text: 'Timeout',      icon: '✗' },
  none:              { color: '#888',    text: 'English',      icon: '—' },
  skipped:           { color: '#888',    text: 'Skipped',      icon: '—' },
}

export function TranslationStatus({
  status,
  polarityInverted,
  method,
  className = '',
}: TranslationStatusProps) {
  const key = method || status
  const config = STATUS_CONFIG[key] || STATUS_CONFIG['none']

  return (
    <span
      className={`translation-status-badge ${className}`}
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        padding: '2px 8px',
        fontSize: '0.72rem',
        fontWeight: 600,
        letterSpacing: '0.3px',
        borderRadius: '9999px',
        border: `1px solid ${config.color}33`,
        background: `${config.color}15`,
        color: config.color,
        whiteSpace: 'nowrap',
      }}
      title={
        polarityInverted
          ? 'Polarity inverted — used original text'
          : `Translation: ${config.text} (${key})`
      }
    >
      <span style={{ fontSize: '0.65rem' }}>{config.icon}</span>
      {config.text}
      {polarityInverted && (
        <span
          style={{
            marginLeft: '2px',
            color: '#FF9800',
            fontSize: '0.65rem',
          }}
          title="Polarity inverted — sentiment may be unreliable"
        >
          ⚠
        </span>
      )}
    </span>
  )
}

export default TranslationStatus
