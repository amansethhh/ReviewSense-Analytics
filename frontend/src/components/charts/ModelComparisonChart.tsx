import { memo } from 'react'
import {
  RadarChart, PolarGrid, PolarAngleAxis,
  Radar, Tooltip, Legend,
  ResponsiveContainer, Customized,
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

/**
 * Renders 25 / 50 / 75 / 100 tick labels along the Accuracy spoke (straight up, 90° from east).
 * At a spoke direction the polygon VERTEX exactly coincides with the circle radius,
 * so labels placed at (cx + offset, cy - r) are pixel-perfect on their ring lines.
 */
function RadiusTickLabels(props: Record<string, unknown>) {
  const cx = props.cx as number | undefined
  const cy = props.cy as number | undefined
  const outerRadius = props.outerRadius as number | undefined
  if (!cx || !cy || !outerRadius) return null

  return (
    <g>
      {[25, 50, 75, 100].map(tick => {
        const r = (tick / 100) * outerRadius
        // Accuracy spoke is straight up → x = cx, y = cy - r
        // Shift 10px right so label doesn't overlap the centre axis
        return (
          <text
            key={tick}
            x={cx + 10}
            y={cy - r}
            textAnchor="start"
            dominantBaseline="middle"
            fill="#6e7681"
            fontSize={9}
            fontFamily="Geist, monospace"
          >
            {tick}
          </text>
        )
      })}
    </g>
  )
}

export const ModelComparisonChart = memo(function ModelComparisonChart({ models }: Props) {
  const metrics = ['Accuracy', 'Macro F1', 'Weighted F1', 'Precision', 'AUC']

  const data = metrics.map(m => {
    const entry: Record<string, number | string> = { metric: m }
    models.forEach(model => {
      if (m === 'Accuracy')    entry[model.name] = model.accuracy
      if (m === 'Macro F1')    entry[model.name] = model.macro_f1 * 100
      if (m === 'Weighted F1') entry[model.name] = model.weighted_f1 * 100
      if (m === 'Precision')   entry[model.name] = model.macro_prec * 100
      if (m === 'AUC')         entry[model.name] = model.auc * 100
    })
    return entry
  })

  return (
    <ResponsiveContainer width="100%" height={400}>
      <RadarChart
        data={data}
        margin={{ top: 32, right: 72, bottom: 24, left: 72 }}
      >
        <PolarGrid stroke="rgba(255,255,255,0.06)" />

        {/* Spoke labels */}
        <PolarAngleAxis
          dataKey="metric"
          tick={{ fill: '#8b949e', fontSize: 12, fontWeight: 500 }}
          tickLine={false}
        />

        {/* Ring value labels — rendered via Customized so they sit exactly on polygon vertices */}
        <Customized component={RadiusTickLabels} />

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
            <span style={{
              color: '#8b949e',
              fontSize: '12px',
              fontFamily: 'Geist, monospace',
            }}>{v}</span>
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
})
