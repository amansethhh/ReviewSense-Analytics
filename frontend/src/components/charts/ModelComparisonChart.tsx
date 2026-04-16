import {
  RadarChart, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, Radar, Tooltip, Legend,
  ResponsiveContainer,
} from 'recharts'
import type { ModelMetric } from '@/types/api.types'

interface Props { models: ModelMetric[] }

const RADAR_COLORS = [
  'rgba(45,212,191,0.8)',
  'rgba(1,105,111,0.8)',
  'rgba(59,130,246,0.8)',
  'rgba(139,92,246,0.8)',
]

const RADAR_FILLS = [
  'rgba(45,212,191,0.2)',
  'rgba(1,105,111,0.2)',
  'rgba(59,130,246,0.2)',
  'rgba(139,92,246,0.2)',
]

export function ModelComparisonChart({ models }: Props) {
  const metrics = ['Accuracy', 'Macro F1', 'Weighted F1',
                   'Precision', 'AUC']
  const data = metrics.map(m => {
    const entry: Record<string, number | string> = {
      metric: m
    }
    models.forEach(model => {
      if (m === 'Accuracy')    entry[model.name] =
        model.accuracy
      if (m === 'Macro F1')    entry[model.name] =
        model.macro_f1 * 100
      if (m === 'Weighted F1') entry[model.name] =
        model.weighted_f1 * 100
      if (m === 'Precision')   entry[model.name] =
        model.macro_prec * 100
      if (m === 'AUC')         entry[model.name] =
        model.auc * 100
    })
    return entry
  })

  return (
    <ResponsiveContainer width="100%" height={340}>
      <RadarChart data={data}>
        <PolarGrid stroke="rgba(255,255,255,0.06)" />
        <PolarAngleAxis dataKey="metric"
          tick={{ fill: '#8b949e',
                  fontSize: 11 }} />
        <PolarRadiusAxis domain={[0, 100]} angle={90}
          tick={{ fill: '#484f58',
                  fontSize: 10 }} />
        {models.map((model, i) => (
          <Radar
            key={model.name}
            name={model.name}
            dataKey={model.name}
            stroke={RADAR_COLORS[i % RADAR_COLORS.length]}
            fill={RADAR_FILLS[i % RADAR_FILLS.length]}
            fillOpacity={1}
            animationDuration={800}
          />
        ))}
        <Legend
          formatter={(v: string) => (
            <span style={{ color: '#8b949e',
                           fontSize: '12px',
                           fontFamily: 'Geist, monospace' }}>{v}</span>
          )}
        />
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
          labelStyle={{ color: '#ffffff', fontWeight: 700 }}
          formatter={(v: number) => [`${v.toFixed(1)}%`, '']}
        />
      </RadarChart>
    </ResponsiveContainer>
  )
}
