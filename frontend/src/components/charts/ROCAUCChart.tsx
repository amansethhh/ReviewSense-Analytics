import {
  LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Legend, ReferenceLine,
} from 'recharts'

interface ModelROC {
  name: string
  auc: number
  color: string
}

interface Props {
  models: ModelROC[]
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

function generateROCPoints(auc: number) {
  return [
    { fpr: 0,   tpr: 0 },
    { fpr: 0.1, tpr: auc * 0.7 },
    { fpr: 0.3, tpr: auc * 0.9 },
    { fpr: 0.7, tpr: auc * 0.98 },
    { fpr: 1,   tpr: 1 },
  ]
}

export function ROCAUCChart({ models }: Props) {
  // Build combined data
  const allPoints = [0, 0.1, 0.3, 0.7, 1]
  const data = allPoints.map((fpr, i) => {
    const entry: Record<string, number> = { fpr }
    models.forEach(m => {
      const pts = generateROCPoints(m.auc)
      entry[m.name] = Number(pts[i].tpr.toFixed(3))
    })
    entry['Random'] = fpr
    return entry
  })

  return (
    <ResponsiveContainer width="100%" height={340}>
      <LineChart data={data} margin={{ left: 10, right: 30 }}>
        <CartesianGrid stroke="rgba(255,255,255,0.04)" />
        <XAxis dataKey="fpr" type="number" domain={[0, 1]}
          tickFormatter={(v: number) => v.toFixed(1)}
          tick={{ fill: '#8b949e', fontSize: 11 }}
          axisLine={false} tickLine={false}
          label={{ value: 'False Positive Rate', position: 'insideBottom',
            offset: -5, fill: '#8b949e', fontSize: 11 }} />
        <YAxis type="number" domain={[0, 1]}
          tickFormatter={(v: number) => v.toFixed(1)}
          tick={{ fill: '#8b949e', fontSize: 11 }}
          axisLine={false} tickLine={false}
          label={{ value: 'True Positive Rate', angle: -90,
            position: 'insideLeft', fill: '#8b949e', fontSize: 11 }} />
        <Tooltip contentStyle={tooltipStyle}
          labelStyle={{ color: '#ffffff', fontWeight: 700 }}
          formatter={(v: number, name: string) => [v.toFixed(3), name]} />
        <Legend formatter={(v: string) => (
          <span style={{ color: '#8b949e', fontSize: '12px',
            fontFamily: 'Geist, monospace' }}>{v}</span>
        )} />
        <ReferenceLine
          segment={[{ x: 0, y: 0 }, { x: 1, y: 1 }]}
          stroke="rgba(255,255,255,0.15)" strokeDasharray="4 4" />
        {models.map(m => (
          <Line key={m.name} type="monotone" dataKey={m.name}
            stroke={m.color} strokeWidth={2} dot={false}
            animationBegin={0} animationDuration={800} />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}
