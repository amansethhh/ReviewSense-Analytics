import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell,
} from 'recharts'

interface FeatureData {
  word: string
  weight: number
}

interface Props {
  features?: FeatureData[]
}

const DEFAULT_FEATURES: FeatureData[] = [
  { word: 'excellent', weight: 0.42 },
  { word: 'terrible', weight: -0.39 },
  { word: 'great', weight: 0.35 },
  { word: 'awful', weight: -0.33 },
  { word: 'amazing', weight: 0.31 },
  { word: 'horrible', weight: -0.29 },
  { word: 'fantastic', weight: 0.27 },
  { word: 'disappointing', weight: -0.25 },
  { word: 'perfect', weight: 0.23 },
  { word: 'worst', weight: -0.22 },
  { word: 'best', weight: 0.20 },
  { word: 'poor', weight: -0.19 },
  { word: 'outstanding', weight: 0.18 },
  { word: 'useless', weight: -0.17 },
  { word: 'recommend', weight: 0.16 },
  { word: 'avoid', weight: -0.15 },
  { word: 'love', weight: 0.14 },
  { word: 'hate', weight: -0.13 },
  { word: 'wonderful', weight: 0.12 },
  { word: 'broken', weight: -0.11 },
]

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
      fontSize: '12px',
    }}>
      <div style={{ color: '#ffffff', fontWeight: 700, marginBottom: '4px' }}>{label}</div>
      <div style={{ color, fontWeight: 600 }}>
        Weight: {val.toFixed(3)}
      </div>
    </div>
  )
}

export function FeatureImportanceChart({ features }: Props) {
  const data = (features ?? DEFAULT_FEATURES).slice(0, 20)

  return (
    <ResponsiveContainer width="100%" height={500}>
      <BarChart data={data} layout="vertical"
                margin={{ left: 10, right: 30 }}>
        <CartesianGrid stroke="rgba(255,255,255,0.04)" horizontal={false} />
        <XAxis type="number"
          tick={{ fill: '#8b949e', fontSize: 11 }}
          axisLine={false} tickLine={false} />
        <YAxis type="category" dataKey="word"
          tick={{ fill: '#e6edf3', fontSize: 11, fontWeight: 600 }}
          axisLine={false} tickLine={false} width={100} />
        <Tooltip content={<CustomTooltip />} />
        <Bar dataKey="weight" radius={[0, 3, 3, 0]}
          animationBegin={0} animationDuration={800}>
          {data.map((entry, i) => (
            <Cell key={i}
              fill={entry.weight >= 0 ? '#22c55e' : '#f43f5e'} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
}
