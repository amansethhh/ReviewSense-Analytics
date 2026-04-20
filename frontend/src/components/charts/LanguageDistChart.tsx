import { memo } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Cell, LabelList,
} from 'recharts'

interface LangDistData {
  language: string
  count: number
  percentage: number
}

interface Props {
  data: LangDistData[]
}

const LANG_COLORS = [
  '#00D9FF', '#2DD4BF', '#818CF8', '#F59E0B',
  '#22C55E', '#F43F5E', '#A78BFA', '#FB923C',
  '#EC4899', '#06B6D4', '#84CC16', '#EF4444',
]

/* eslint-disable @typescript-eslint/no-explicit-any */
function CustomTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  const entry = payload[0]
  const idx = entry?.payload?._idx ?? 0
  const color = LANG_COLORS[idx % LANG_COLORS.length]
  return (
    <div style={{
      background: 'rgba(13,17,23,0.96)',
      border: `1px solid ${color}40`,
      borderRadius: '10px',
      boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
      padding: '10px 14px',
      fontFamily: 'Geist, monospace',
      fontSize: '12px',
    }}>
      <div style={{ color: '#ffffff', fontWeight: 700, marginBottom: '4px' }}>{label}</div>
      <div style={{ color, fontWeight: 600 }}>
        {entry.value} reviews ({entry.payload?.percentage ?? 0}%)
      </div>
    </div>
  )
}

export const LanguageDistChart = memo(function LanguageDistChart({ data }: Props) {
  if (!data.length) return null
  const indexed = data.map((d, i) => ({ ...d, _idx: i }))

  return (
    <ResponsiveContainer width="100%" height={Math.max(220, data.length * 42 + 40)}>
      <BarChart data={indexed} layout="vertical"
                margin={{ left: 10, right: 55, top: 5, bottom: 5 }}>
        <CartesianGrid stroke="rgba(255,255,255,0.04)" horizontal={false} />
        <XAxis type="number"
          tick={{ fill: '#8b949e', fontSize: 11 }}
          axisLine={false} tickLine={false}
          domain={[0, 'dataMax']}
        />
        <YAxis type="category" dataKey="language"
          tick={{ fill: '#e6edf3', fontSize: 12, fontWeight: 600 }}
          axisLine={false} tickLine={false} width={90} />
        <Tooltip content={<CustomTooltip />} />
        <Bar dataKey="count" name="Reviews" radius={[0, 6, 6, 0]}
             animationBegin={0} animationDuration={900}
             animationEasing="ease-out">
          {indexed.map((_, i) => (
            <Cell key={`ld-${i}`} fill={LANG_COLORS[i % LANG_COLORS.length]} />
          ))}
          <LabelList
            dataKey="percentage"
            position="right"
            formatter={(v: number) => `${v}%`}
            style={{ fill: '#e6edf3', fontSize: 11, fontWeight: 600 }}
          />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  )
})
