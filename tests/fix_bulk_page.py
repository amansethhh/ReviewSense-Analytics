"""Replace STATE 3 processing section in BulkAnalysisPage.tsx with AnalysisLayout component."""
import os

filepath = r"w:\ReviewSense-Analytics\frontend\src\pages\BulkAnalysisPage.tsx"

with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Add AnalysisLayout import after line 11 (CyberCard import)
# Find the CyberCard import line
for i, line in enumerate(lines):
    if "import { SentimentPieChart }" in line:
        import_line_idx = i
        break

# Insert AnalysisLayout import
import_stmt = "import { AnalysisLayout } from '@/components/layout/AnalysisLayout'\n"
lines.insert(import_line_idx + 1, import_stmt)

# Now find STATE 3 markers (adjusted +1 due to insertion)
state3_start = None
state3_end = None
for i, line in enumerate(lines):
    if '{/* STATE 3: PROCESSING' in line:
        state3_start = i
    if state3_start and '      {/* STATE 4: RESULTS */' in line:
        state3_end = i
        break

print(f"STATE 3: lines {state3_start+1} to {state3_end}")

new_state3 = '''      {/* STATE 3: PROCESSING — Uses shared AnalysisLayout */}
      {stage === 'processing' && (() => {
        const rows = result?.results ?? []
        const processed = result?.processed ?? 0
        const total = result?.total_rows ?? 0
        const progressPct = result?.progress ? Math.round(result.progress) : (total > 0 ? Math.round((processed / total) * 100) : 0)
        const speed = elapsed > 0 ? (processed / elapsed).toFixed(1) : '0.0'
        const avgConf = rows.length > 0 ? (rows.reduce((s: number, r: any) => s + r.confidence, 0) / rows.length).toFixed(1) : '\\u2014'
        const errorCount = rows.filter((r: any) => r.sentiment === 'error' || r.sentiment === 'unknown').length

        const posCount     = result?.live_pos     ?? rows.filter((r: any) => r.sentiment === 'positive').length
        const negCount     = result?.live_neg     ?? rows.filter((r: any) => r.sentiment === 'negative').length
        const neuCount     = result?.live_neu     ?? rows.filter((r: any) => r.sentiment === 'neutral').length
        const sarcasmCount = result?.live_sarcasm ?? rows.filter((r: any) => r.sarcasm_detected).length
        const sentRealTotal = posCount + negCount + neuCount
        const hasSentimentData = sentRealTotal > 0
        const sentTotal = sentRealTotal || 1
        const posPct = Math.round((posCount / sentTotal) * 100)
        const negPct = Math.round((negCount / sentTotal) * 100)
        const neuPct = 100 - posPct - negPct

        return (
          <AnalysisLayout
            processed={processed}
            total={total}
            speed={speed}
            avgConf={avgConf}
            errorCount={errorCount}
            progressPct={progressPct}
            configRows={[
              ['Model', model === 'best' ? 'Best' : formatModelName(model)],
              ['Multi', isMultilingual ? 'ON' : 'OFF'],
              ['ABSA', runAbsa ? 'ON' : 'OFF'],
              ['Sarcasm', runSarcasm ? 'ON' : 'OFF'],
            ]}
            hasSentimentData={hasSentimentData}
            posPct={posPct}
            neuPct={neuPct}
            negPct={negPct}
            sentTotal={sentRealTotal}
            pipelineRows={[
              { label: 'Positive', value: posCount, color: '#22c55e' },
              { label: 'Neutral', value: neuCount, color: '#f59e0b' },
              { label: 'Negative', value: negCount, color: '#f43f5e' },
              { label: 'Sarcasm', value: sarcasmCount, color: '#a78bfa' },
            ]}
            phase={result?.phase}
            elapsed={elapsed}
            logs={logs}
            prevLogCount={prevLogCount}
            isFailed={result?.status === 'failed'}
            failError={result?.error ?? undefined}
            onCancel={handleReset}
            onRetry={handleReset}
          />
        )
      })()}

'''

# Replace lines
lines[state3_start:state3_end] = [new_state3]

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"SUCCESS: Replaced STATE 3 ({state3_end - state3_start} lines) with AnalysisLayout ({new_state3.count(chr(10))} lines)")
