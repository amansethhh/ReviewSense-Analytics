import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell,
} from 'recharts'
import type { LIMEFeature } from '@/types/api.types'

interface Props { features: LIMEFeature[] }

/* eslint-disable @typescript-eslint/no-explicit-any */
function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  const val = payload[0].value
  const color = val >= 0 ? '#22c55e' : '#f43f5e'
  return (
    <div style={{
      background: 'rgba(22,27,34,0.95)',
      border: `1px solid ${color}40`,
      borderRadius: '10px',
      boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
      padding: '10px 14px',
      fontFamily: 'Geist, monospace',
      fontSize: '13px',
    }}>
      <div style={{ color: '#ffffff', fontWeight: 700, marginBottom: '4px' }}>{label}</div>
      <div style={{ color, fontWeight: 600 }}>
        Impact: {val.toFixed(4)}
      </div>
    </div>
  )
}

export function LIMEChart({ features }: Props) {
  const sorted = [...features]
    .sort((a, b) => Math.abs(b.weight) - Math.abs(a.weight))
    .slice(0, 10)

  const data = sorted.map(f => ({
    word:   f.word,
    weight: Number(f.weight.toFixed(4)),
  }))

  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data} layout="vertical"
                margin={{ left: 20, right: 30 }}>
        <CartesianGrid strokeDasharray="3 3"
          stroke="rgba(255,255,255,0.06)" horizontal={false} />
        <XAxis type="number"
          tick={{ fill: '#8b949e', fontSize: 11 }}
          axisLine={false} tickLine={false} />
        <YAxis type="category" dataKey="word"
          tick={{ fill: '#e6edf3', fontSize: 12, fontWeight: 600 }}
          axisLine={false} tickLine={false} width={80} />
        <Tooltip content={<CustomTooltip />} />
        <Bar dataKey="weight" radius={[0,3,3,0]}
             animationBegin={100}
             animationDuration={600}>
          {data.map((entry, i) => (
            <Cell key={i}
              fill={entry.weight >= 0
                ? '#22c55e'
                : '#f43f5e'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
