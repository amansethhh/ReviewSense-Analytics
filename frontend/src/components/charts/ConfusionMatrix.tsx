import React from 'react'
import type { ConfusionMatrixData } from '@/types/api.types'

interface Props { data: ConfusionMatrixData }

export function ConfusionMatrix({ data }: Props) {
  const maxVal = Math.max(...data.matrix.flat())

  return (
    <div className="cm-wrap">
      <p className="cm-title">{data.model_name}</p>
      <div className="cm-grid"
           style={{
             gridTemplateColumns: `auto repeat(${
               data.labels.length}, 1fr)`,
           }}>
        {/* corner cell */}
        <div className="cm-cell cm-cell--header" />
        {/* column headers */}
        {data.labels.map(l => (
          <div key={`col-${l}`}
               className="cm-cell cm-cell--header">
            {l.slice(0,3)}
          </div>
        ))}
        {/* rows */}
        {data.matrix.map((row, ri) => (
          <React.Fragment key={`row-${ri}`}>
            <div className="cm-cell cm-cell--rowlabel">
              {data.labels[ri].slice(0,3)}
            </div>
            {row.map((cell, ci) => {
              const intensity = maxVal > 0
                ? cell / maxVal : 0
              const bg = ri === ci
                ? `rgba(1,105,111,${0.15 + intensity * 0.7})`
                : `rgba(248,81,73,${intensity * 0.4})`
              return (
                <div key={ci} className="cm-cell"
                     style={{ background: bg }}>
                  {cell.toLocaleString()}
                </div>
              )
            })}
          </React.Fragment>
        ))}
      </div>
    </div>
  )
}
