import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend,
} from 'recharts'

interface TrendPoint {
  month: string
  positive: number
  negative: number
  neutral: number
}

interface Props {
  data?: TrendPoint[]
}

const tooltipStyle = {
  background: 'rgba(22,27,34,0.95)',
  border: '1px solid rgba(255,255,255,0.08)',
  borderRadius: '10px',
  boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
  fontFamily: 'Geist, monospace',
  fontSize: '12px',
  color: '#e6edf3',
}

export function SentimentTrendChart({ data }: Props) {
  // No data — render an awaiting state instead of fake default months
  if (!data || data.length === 0) {
    return (
      <div style={{
        height: 300,
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '12px',
        color: 'var(--color-text-faint)',
      }}>
        <div style={{
          width: '52px',
          height: '52px',
          borderRadius: '50%',
          border: '2px dashed rgba(0,217,255,0.25)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          animation: 'pulse 2s ease-in-out infinite',
        }}>
          <svg width="22" height="22" viewBox="0 0 48 48" fill="none">
            <path d="M6 38l10-14 8 6 8-12 10-8" stroke="rgba(0,217,255,0.5)"
              strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <div style={{ fontSize: '12px', textAlign: 'center', lineHeight: 1.5 }}>
          <div style={{ color: 'var(--color-text-muted)', fontWeight: 600 }}>No trend data yet</div>
          <div style={{ fontSize: '11px', marginTop: '4px', color: 'var(--color-text-faint)' }}>
            Run a batch analysis to generate sentiment trends
          </div>
        </div>
      </div>
    )
  }

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data} margin={{ left: 10, right: 30 }}>
        <CartesianGrid stroke="rgba(255,255,255,0.04)" />
        <XAxis dataKey="month"
          tick={{ fill: '#8b949e', fontSize: 11 }}
          axisLine={false} tickLine={false} />
        <YAxis
          tick={{ fill: '#8b949e', fontSize: 11 }}
          axisLine={false} tickLine={false}
          tickFormatter={(v: number) => `${v}%`} />
        <Tooltip contentStyle={tooltipStyle}
          labelStyle={{ color: '#ffffff', fontWeight: 700 }}
          formatter={(v: number) => [`${v}%`, '']} />
        <Legend formatter={(v: string) => (
          <span style={{ color: '#8b949e', fontSize: '12px',
            fontFamily: 'Geist, monospace' }}>{v}</span>
        )} />
        <Line type="monotone" dataKey="positive" name="Positive"
          stroke="#22c55e" strokeWidth={2} dot={{ r: 3 }}
          animationBegin={0} animationDuration={800} />
        <Line type="monotone" dataKey="negative" name="Negative"
          stroke="#f43f5e" strokeWidth={2} dot={{ r: 3 }}
          animationBegin={0} animationDuration={800} />
        <Line type="monotone" dataKey="neutral" name="Neutral"
          stroke="#f59e0b" strokeWidth={2} dot={{ r: 3 }}
          animationBegin={0} animationDuration={800} />
      </LineChart>
    </ResponsiveContainer>
  )
}
