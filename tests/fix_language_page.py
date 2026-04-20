"""Replace processing section in LanguageAnalysisPage.tsx with AnalysisLayout component."""
import os

filepath = r"w:\ReviewSense-Analytics\frontend\src\pages\LanguageAnalysisPage.tsx"

with open(filepath, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Add AnalysisLayout import after line 14 (SentimentPieChart import)
for i, line in enumerate(lines):
    if "import { SentimentPieChart }" in line:
        import_line_idx = i
        break

# Insert AnalysisLayout import
import_stmt = "import { AnalysisLayout } from '@/components/layout/AnalysisLayout'\n"
lines.insert(import_line_idx + 1, import_stmt)

# Find STATE 3 markers (adjusted +1 due to insertion)
state3_start = None
state3_end = None
for i, line in enumerate(lines):
    if "{bStage === 'processing' && (() => {" in line:
        state3_start = i
    if state3_start and "          {bStage === 'results' && bResult?.summary && (" in line:
        state3_end = i
        break

print(f"STATE 3: lines {state3_start+1} to {state3_end}")

new_state3 = '''          {bStage === 'processing' && (() => {
            const rows = bResult?.results ?? []
            const processed = bResult?.processed ?? 0
            const total = bResult?.total_rows ?? 0
            const progressPct = bResult?.progress ? Math.round(bResult.progress) : (total > 0 ? Math.round((processed / total) * 100) : 0)
            const speed = bElapsed > 0 ? (processed / bElapsed).toFixed(1) : '0.0'
            const avgConf = rows.length > 0 ? (rows.reduce((s: number, r: any) => s + r.confidence, 0) / rows.length).toFixed(1) : '\\u2014'
            const errorCount = rows.filter((r: any) => r.sentiment === 'error' || r.sentiment === 'unknown').length

            const posCount     = bResult?.live_pos     ?? rows.filter((r: any) => r.sentiment === 'positive').length
            const negCount     = bResult?.live_neg     ?? rows.filter((r: any) => r.sentiment === 'negative').length
            const neuCount     = bResult?.live_neu     ?? rows.filter((r: any) => r.sentiment === 'neutral').length
            const sarcasmCount = bResult?.live_sarcasm ?? rows.filter((r: any) => r.sarcasm_detected).length
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
                  ['Mode', 'Multilingual'],
                  ['Routing', 'Auto-Detect'],
                  ['Target', bTargetLang.toUpperCase()],
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
                phase={bResult?.phase}
                elapsed={bElapsed}
                logs={bLogs}
                prevLogCount={prevLogCount}
                isFailed={bResult?.status === 'failed'}
                failError={bResult?.error ?? undefined}
                onCancel={handleBReset}
                onRetry={handleBReset}
              />
            )
          })()}

'''

# Replace lines
lines[state3_start:state3_end] = [new_state3]

with open(filepath, 'w', encoding='utf-8') as f:
    f.writelines(lines)

print(f"SUCCESS: Replaced STATE 3 ({state3_end - state3_start} lines) with AnalysisLayout ({new_state3.count(chr(10))} lines)")
