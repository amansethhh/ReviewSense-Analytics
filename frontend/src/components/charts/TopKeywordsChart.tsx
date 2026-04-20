import { memo } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell,
} from 'recharts'

interface KeywordData {
  word: string
  positive: number
  negative: number
}

interface Props {
  keywords: KeywordData[]
}

/* eslint-disable @typescript-eslint/no-explicit-any */
function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div style={{
      background: 'rgba(22,27,34,0.95)',
      border: '1px solid rgba(255,255,255,0.08)',
      borderRadius: '10px',
      boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
      padding: '10px 14px',
      fontFamily: 'Geist, monospace',
      fontSize: '12px',
    }}>
      <div style={{ color: '#ffffff', fontWeight: 700, marginBottom: '4px' }}>{label}</div>
      {payload.map((entry: any, i: number) => (
        <div key={i} style={{ color: entry.color, fontWeight: 600 }}>
          {entry.name}: {entry.value}
        </div>
      ))}
    </div>
  )
}

export const TopKeywordsChart = memo(function TopKeywordsChart({ keywords }: Props) {
  const data = keywords.slice(0, 10)

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} layout="vertical"
                margin={{ left: 20, right: 30 }}>
        <CartesianGrid stroke="rgba(255,255,255,0.04)" horizontal={false} />
        <XAxis type="number"
          tick={{ fill: '#8b949e', fontSize: 11 }}
          axisLine={false} tickLine={false} />
        <YAxis type="category" dataKey="word"
          tick={{ fill: '#e6edf3', fontSize: 11, fontWeight: 600 }}
          axisLine={false} tickLine={false} width={80} />
        <Tooltip content={<CustomTooltip />} />
        <Bar dataKey="positive" name="Positive" fill="#22c55e"
          radius={[0, 3, 3, 0]} animationBegin={0} animationDuration={800}>
          {data.map((_, i) => (
            <Cell key={`p-${i}`} fill="#22c55e" />
          ))}
        </Bar>
        <Bar dataKey="negative" name="Negative" fill="#f43f5e"
          radius={[0, 3, 3, 0]} animationBegin={0} animationDuration={800}>
          {data.map((_, i) => (
            <Cell key={`n-${i}`} fill="#f43f5e" />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
})
