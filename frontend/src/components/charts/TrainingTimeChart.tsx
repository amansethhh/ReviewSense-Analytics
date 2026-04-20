import { memo } from 'react'
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer,
} from 'recharts'

const tooltipStyle = {
  background: 'rgba(22,27,34,0.95)',
  border: '1px solid rgba(255,255,255,0.08)',
  borderRadius: '10px',
  boxShadow: '0 8px 32px rgba(0,0,0,0.6)',
  fontFamily: 'Geist, monospace',
  fontSize: '12px',
  color: '#e6edf3',
}

const DATA = [
  { name: 'Linear SVC', time: 0.8 },
  { name: 'LogReg',    time: 1.2 },
  { name: 'NaiveBayes', time: 0.3 },
  { name: 'RandomForest', time: 4.7 },
]

export const TrainingTimeChart = memo(function TrainingTimeChart() {
  return (
    <ResponsiveContainer width="100%" height={280}>
      <BarChart data={DATA} margin={{ left: 10, right: 30, bottom: 5 }}>
        <CartesianGrid stroke="rgba(255,255,255,0.04)" horizontal />
        <XAxis dataKey="name"
          tick={{ fill: '#8b949e', fontSize: 11 }}
          axisLine={false} tickLine={false} />
        <YAxis
          tick={{ fill: '#8b949e', fontSize: 11 }}
          axisLine={false} tickLine={false}
          label={{ value: 'Training Time (s)', angle: -90,
            position: 'insideLeft', fill: '#8b949e', fontSize: 11 }} />
        <Tooltip contentStyle={tooltipStyle}
          labelStyle={{ color: '#ffffff', fontWeight: 700 }}
          formatter={(v: number) => [`${v}s`, 'Time']} />
        <Bar dataKey="time" fill="url(#tealGrad)"
          radius={[4, 4, 0, 0]}
          animationBegin={0} animationDuration={800} />
        <defs>
          <linearGradient id="tealGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#2dd4bf" />
            <stop offset="100%" stopColor="#01696f" />
          </linearGradient>
        </defs>
      </BarChart>
    </ResponsiveContainer>
  )
})
