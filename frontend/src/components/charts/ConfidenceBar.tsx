import { memo } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell,
} from 'recharts'

interface Props {
  probabilities: Record<string, number>
}

const COLORS: Record<string, string> = {
  positive: '#22c55e',
  negative: '#f43f5e',
  neutral:  '#f59e0b',
}

export const ConfidenceBar = memo(function ConfidenceBar({ probabilities }: Props) {
  const data = Object.entries(probabilities).map(
    ([label, value]) => ({
      label: label.charAt(0).toUpperCase() + label.slice(1),
      value: Number((value * 100).toFixed(2)),
      key:   label,
    })
  )

  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={data} layout="vertical"
                margin={{ left: 10, right: 30 }}>
        <CartesianGrid strokeDasharray="3 3"
          stroke="rgba(255,255,255,0.06)" horizontal={false} />
        <XAxis type="number" domain={[0, 100]}
          tickFormatter={(v: number) => `${v}%`}
          tick={{ fill: '#8b949e', fontSize: 12 }}
          axisLine={false} tickLine={false} />
        <YAxis type="category" dataKey="label"
          tick={{ fill: '#8b949e', fontSize: 12 }}
          axisLine={false} tickLine={false} width={70} />
        <Tooltip
          contentStyle={{
            background: 'rgba(22,27,34,0.95)',
            border: '1px solid rgba(255,255,255,0.08)',
            borderRadius: '10px',
            boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
            fontFamily: 'Geist, monospace',
            fontSize: '13px',
            color: '#e6edf3',
          }}
          formatter={(v: number) => [`${v}%`, 'Confidence']}
        />
        <Bar dataKey="value" radius={[0,4,4,0]}
             animationBegin={100}
             animationDuration={600}>
          {data.map(entry => (
            <Cell key={entry.key}
              fill={COLORS[entry.key] ?? '#8b949e'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
})
