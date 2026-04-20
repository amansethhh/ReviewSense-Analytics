import { memo } from 'react'
import {
  PieChart, Pie, Cell, Tooltip,
  ResponsiveContainer, Legend,
} from 'recharts'

const COLORS: Record<string, string> = {
  positive: '#22c55e',
  negative: '#f43f5e',
  neutral:  '#f59e0b',
}

interface Props {
  positive: number
  negative: number
  neutral:  number
}

/* eslint-disable @typescript-eslint/no-explicit-any */
function CustomTooltip({ active, payload }: any) {
  if (!active || !payload?.length) return null
  const entry = payload[0]
  const color = COLORS[entry.name?.toLowerCase()] ?? '#8b949e'
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
      <div style={{ color: '#ffffff', fontWeight: 700, marginBottom: '4px' }}>{entry.name}</div>
      <div style={{ color, fontWeight: 600 }}>
        {entry.value.toFixed(1)}%
      </div>
    </div>
  )
}

export const SentimentPieChart = memo(function SentimentPieChart({
  positive, negative, neutral,
}: Props) {
  const data = [
    { name: 'Positive', value: positive },
    { name: 'Negative', value: negative },
    { name: 'Neutral',  value: neutral },
  ].filter(d => d.value > 0)

  return (
    <ResponsiveContainer width="100%" height={260}>
      <PieChart>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={100}
          paddingAngle={3}
          dataKey="value"
          animationBegin={0}
          animationDuration={800}
          animationEasing="ease-out"
        >
          {data.map(entry => (
            <Cell
              key={entry.name}
              fill={COLORS[entry.name.toLowerCase()]
                ?? '#8b949e'}
            />
          ))}
        </Pie>
        <Tooltip content={<CustomTooltip />} />
        <Legend
          formatter={(value) => (
            <span style={{ color: COLORS[value.toLowerCase()] ?? '#8b949e',
                           fontSize: '13px',
                           fontFamily: 'Geist, sans-serif',
                           fontWeight: 600 }}>
              {value}
            </span>
          )}
        />
      </PieChart>
    </ResponsiveContainer>
  )
})
