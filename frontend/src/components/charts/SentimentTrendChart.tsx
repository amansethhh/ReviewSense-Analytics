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

const DEFAULT_DATA: TrendPoint[] = [
  { month: 'Oct', positive: 42, negative: 28, neutral: 30 },
  { month: 'Nov', positive: 38, negative: 32, neutral: 30 },
  { month: 'Dec', positive: 45, negative: 25, neutral: 30 },
  { month: 'Jan', positive: 40, negative: 30, neutral: 30 },
  { month: 'Feb', positive: 44, negative: 27, neutral: 29 },
  { month: 'Mar', positive: 48, negative: 22, neutral: 30 },
]

export function SentimentTrendChart({ data }: Props) {
  const chartData = data ?? DEFAULT_DATA

  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={chartData} margin={{ left: 10, right: 30 }}>
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
