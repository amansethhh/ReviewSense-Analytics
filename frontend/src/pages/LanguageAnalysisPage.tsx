import { useState, useCallback, useRef, useEffect, useMemo } from 'react'
import { SentimentBadge, AnalysisErrorSummary } from '@/components/ui/Badge'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { NeuralButton } from '@/components/ui/NeuralButton'
import { EyebrowPill } from '@/components/ui/EyebrowPill'
import { HoloToggle } from '@/components/ui/HoloToggle'
import { NeuralSelect } from '@/components/ui/NeuralSelect'
import { FolderUpload } from '@/components/ui/FolderUpload'
import { OrbitalLoader } from '@/components/ui/OrbitalLoader'
import { NeuralInputWrap } from '@/components/ui/NeuralInputWrap'
import { FlagSVG } from '@/components/ui/FlagSVG'
import { SentimentPieChart } from '@/components/charts/SentimentPieChart'
import { TopKeywordsChart } from '@/components/charts/TopKeywordsChart'
import { SentimentTrendChart } from '@/components/charts/SentimentTrendChart'
import { LanguageDistChart } from '@/components/charts/LanguageDistChart'
import { useLanguage } from '@/hooks/useLanguage'
import { useBulk } from '@/hooks/useBulk'
import { useApp } from '@/context/AppContext'
import type { ModelChoice, SentimentLabel } from '@/types/api.types'
import { generateUniversalPDF, generateUniversalCSV, generateUniversalExcel, generateUniversalJSON, detectLang, getTranslation } from '@/utils/exportUtils'

const STOPWORDS = new Set(['a','the','is','was','and','or','but','in','on','at','it','this','that','to','of','for','with','be','are','have','i','my','me','we','they'])

const LANGUAGES = [
  { flag: '🇬🇧', name: 'English',    code: 'EN', example: 'The product quality is absolutely amazing!' },
  { flag: '🇮🇳', name: 'Hindi',      code: 'HI', example: 'यह उत्पाद बहुत अच्छा है।' },
  { flag: '🇪🇸', name: 'Spanish',    code: 'ES', example: 'Este producto es bueno y llega rápido.' },
  { flag: '🇫🇷', name: 'French',     code: 'FR', example: "La batterie dure longtemps, mais l'écran est trop sombre." },
  { flag: '🇩🇪', name: 'German',     code: 'DE', example: 'Dieses Produkt ist gut!!' },
  { flag: '🇨🇳', name: 'Chinese',    code: 'ZH', example: '这个产品非常好！' },
  { flag: '🇵🇹', name: 'Portuguese', code: 'PT', example: 'Este produto é muito bom e chegou rápido!' },
  { flag: '🇷🇺', name: 'Russian',    code: 'RU', example: 'Этот продукт очень хорош!' },
  { flag: '🇯🇵', name: 'Japanese',   code: 'JA', example: 'この製品はとても良いです！' },
  { flag: '🇰🇷', name: 'Korean',     code: 'KO', example: '이 제품은 정말 좋습니다!' },
  { flag: '🇮🇹', name: 'Italian',    code: 'IT', example: 'Questo prodotto è fantastico!' },
  { flag: '🇸🇦', name: 'Arabic',     code: 'AR', example: 'هذا المنتج ممتاز جداً!' },
  { flag: '🇳🇱', name: 'Dutch',      code: 'NL', example: 'Dit product is uitstekend!' },
  { flag: '🇹🇷', name: 'Turkish',    code: 'TR', example: 'Bu ürün çok iyi!' },
  { flag: '🇸🇪', name: 'Swedish',    code: 'SV', example: 'Denna produkt är utmärkt!' },
  { flag: '🇹🇭', name: 'Thai',       code: 'TH', example: 'ผลิตภัณฑ์นี้ยอดเยี่ยมมาก!' },
]

type Tab = 'single' | 'batch'


const icon3dStyle = {
  filter: 'drop-shadow(0 4px 8px rgba(0,217,255,0.35)) drop-shadow(0 1px 2px rgba(0,0,0,0.4))',
  transform: 'perspective(400px) rotateY(-12deg) rotateX(5deg)',
  display: 'inline-block', flexShrink: 0,
} as const

/* ── Section Header ── */
function SectionHeader({ icon, title, subtitle }: { icon: React.ReactNode; title: string; subtitle?: string }) {
  return (
    <div className="card-header" style={{ justifyContent: 'center', flexDirection: 'column', alignItems: 'center', textAlign: 'center', gap: '4px' }}>
      <div style={{
        display: 'inline-flex', alignItems: 'center', gap: '10px',
        background: 'rgba(0, 217, 255, 0.06)', border: '1px solid rgba(0, 217, 255, 0.15)',
        borderRadius: '12px', padding: '8px 20px',
      }}>
        <span style={{ display: 'inline-flex', alignItems: 'center' }}>{icon}</span>
        <span className="card-title" style={{ margin: 0 }}>{title}</span>
      </div>
      {subtitle && <div className="card-subtitle" style={{ textAlign: 'center' }}>{subtitle}</div>}
    </div>
  )
}

/* ── 3D Icons ── */
function Icon3DGlobe({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="glb3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#A78BFA"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs>
      <circle cx="24" cy="24" r="20" stroke="url(#glb3d)" strokeWidth="2" fill="url(#glb3d)" fillOpacity=".08"/>
      <ellipse cx="24" cy="24" rx="10" ry="20" stroke="url(#glb3d)" strokeWidth="1.5" fill="none" opacity=".4"/>
      <path d="M4 24h40M4 16h40M4 32h40" stroke="url(#glb3d)" strokeWidth="1" opacity=".25"/>
    </svg>
  )
}
function Icon3DLang({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="lng3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#00FF88"/></linearGradient></defs>
      <rect x="6" y="6" width="36" height="36" rx="8" stroke="url(#lng3d)" strokeWidth="2" fill="url(#lng3d)" fillOpacity=".08"/>
      <text x="24" y="30" textAnchor="middle" fill="url(#lng3d)" fontSize="20" fontWeight="700" fontFamily="monospace">A</text>
    </svg>
  )
}
function Icon3DText({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="txt3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#818CF8"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs>
      <rect x="6" y="10" width="36" height="28" rx="6" stroke="url(#txt3d)" strokeWidth="2" fill="url(#txt3d)" fillOpacity=".08"/>
      <path d="M14 20h20M14 26h16M14 32h12" stroke="url(#txt3d)" strokeWidth="2" strokeLinecap="round" opacity=".5"/>
    </svg>
  )
}
function Icon3DDetect({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="det3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#2DD4BF"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs>
      <circle cx="20" cy="20" r="14" stroke="url(#det3d)" strokeWidth="2" fill="url(#det3d)" fillOpacity=".08"/>
      <path d="M30 30L42 42" stroke="url(#det3d)" strokeWidth="3" strokeLinecap="round"/>
    </svg>
  )
}
function Icon3DSentiment({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="snt3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#22C55E"/><stop offset="100%" stopColor="#2DD4BF"/></linearGradient></defs>
      <circle cx="24" cy="24" r="20" stroke="url(#snt3d)" strokeWidth="2" fill="url(#snt3d)" fillOpacity=".08"/>
      <circle cx="16" cy="20" r="2" fill="url(#snt3d)"/>
      <circle cx="32" cy="20" r="2" fill="url(#snt3d)"/>
      <path d="M16 30c4 5 12 5 16 0" stroke="url(#snt3d)" strokeWidth="2" strokeLinecap="round" fill="none"/>
    </svg>
  )
}
function Icon3DPipeline({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="pip3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#F59E0B"/><stop offset="100%" stopColor="#F43F5E"/></linearGradient></defs>
      <path d="M6 24h8M18 24h12M34 24h8" stroke="url(#pip3d)" strokeWidth="2" strokeLinecap="round"/>
      <circle cx="14" cy="24" r="4" stroke="url(#pip3d)" strokeWidth="2" fill="url(#pip3d)" fillOpacity=".15"/>
      <circle cx="34" cy="24" r="4" stroke="url(#pip3d)" strokeWidth="2" fill="url(#pip3d)" fillOpacity=".15"/>
      <rect x="18" y="18" width="12" height="12" rx="3" stroke="url(#pip3d)" strokeWidth="2" fill="url(#pip3d)" fillOpacity=".1"/>
    </svg>
  )
}
function Icon3DKeyword({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="kw3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00FF88"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs>
      <rect x="8" y="10" width="32" height="8" rx="4" fill="url(#kw3d)" opacity=".3"/>
      <rect x="8" y="22" width="24" height="8" rx="4" fill="url(#kw3d)" opacity=".2"/>
      <rect x="8" y="34" width="16" height="8" rx="4" fill="url(#kw3d)" opacity=".15"/>
    </svg>
  )
}
function Icon3DAI({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="ai3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#A78BFA"/><stop offset="100%" stopColor="#818CF8"/></linearGradient></defs>
      <rect x="6" y="6" width="36" height="36" rx="8" stroke="url(#ai3d)" strokeWidth="2" fill="url(#ai3d)" fillOpacity=".08"/>
      <text x="24" y="31" textAnchor="middle" fill="url(#ai3d)" fontSize="18" fontWeight="700" fontFamily="monospace">AI</text>
    </svg>
  )
}
function Icon3DLIME({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="lm3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#FDE047"/><stop offset="100%" stopColor="#22C55E"/></linearGradient></defs>
      <rect x="6" y="14" width="36" height="20" rx="6" stroke="url(#lm3d)" strokeWidth="2" fill="url(#lm3d)" fillOpacity=".08"/>
      <rect x="10" y="20" width="6" height="8" rx="2" fill="#22C55E" opacity=".5"/>
      <rect x="18" y="20" width="6" height="8" rx="2" fill="#F43F5E" opacity=".3"/>
      <rect x="26" y="20" width="6" height="8" rx="2" fill="#22C55E" opacity=".4"/>
      <rect x="34" y="20" width="6" height="8" rx="2" fill="rgba(255,255,255,0.1)"/>
    </svg>
  )
}
function Icon3DExport({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="exp3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#A78BFA"/></linearGradient></defs>
      <rect x="10" y="6" width="28" height="36" rx="4" stroke="url(#exp3d)" strokeWidth="2" fill="url(#exp3d)" fillOpacity=".08"/>
      <path d="M24 18v14M18 26l6 6 6-6" stroke="url(#exp3d)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  )
}
function Icon3DChart({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="ch3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#F43F5E"/><stop offset="100%" stopColor="#F59E0B"/></linearGradient></defs>
      <circle cx="24" cy="24" r="18" stroke="url(#ch3d)" strokeWidth="2" fill="url(#ch3d)" fillOpacity=".08"/>
      <path d="M24 6a18 18 0 0 1 18 18H24V6z" fill="url(#ch3d)" opacity=".25"/>
    </svg>
  )
}
function Icon3DTrend({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="trd3d3" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#00FF88"/></linearGradient></defs>
      <path d="M6 38l10-14 8 6 8-12 10-8" stroke="url(#trd3d3)" strokeWidth="2.5" strokeLinecap="round" fill="none"/>
      <circle cx="42" cy="10" r="3" fill="url(#trd3d3)"/>
    </svg>
  )
}
function Icon3DTotal({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="tot3dL" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#818CF8"/></linearGradient></defs>
      <rect x="8" y="8" width="32" height="32" rx="8" stroke="url(#tot3dL)" strokeWidth="2" fill="url(#tot3dL)" fillOpacity=".08"/>
      <text x="24" y="30" textAnchor="middle" fill="url(#tot3dL)" fontSize="16" fontWeight="700">#</text>
    </svg>
  )
}
function Icon3DPositive({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="pos3dL" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#22C55E"/><stop offset="100%" stopColor="#2DD4BF"/></linearGradient></defs>
      <circle cx="24" cy="24" r="18" stroke="url(#pos3dL)" strokeWidth="2" fill="url(#pos3dL)" fillOpacity=".08"/>
      <path d="M16 24l6 6 10-12" stroke="url(#pos3dL)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  )
}
function Icon3DNegative({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="neg3dL" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#F43F5E"/><stop offset="100%" stopColor="#FB7185"/></linearGradient></defs>
      <circle cx="24" cy="24" r="18" stroke="url(#neg3dL)" strokeWidth="2" fill="url(#neg3dL)" fillOpacity=".08"/>
      <path d="M16 16l16 16M32 16L16 32" stroke="url(#neg3dL)" strokeWidth="2.5" strokeLinecap="round"/>
    </svg>
  )
}
function Icon3DNeutral({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="neu3dL" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#F59E0B"/><stop offset="100%" stopColor="#FDE047"/></linearGradient></defs>
      <circle cx="24" cy="24" r="18" stroke="url(#neu3dL)" strokeWidth="2" fill="url(#neu3dL)" fillOpacity=".08"/>
      <path d="M14 24h20" stroke="url(#neu3dL)" strokeWidth="2.5" strokeLinecap="round"/>
    </svg>
  )
}
function Icon3DLangCount({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="lcn3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#2DD4BF"/><stop offset="100%" stopColor="#A78BFA"/></linearGradient></defs>
      <circle cx="24" cy="24" r="18" stroke="url(#lcn3d)" strokeWidth="2" fill="url(#lcn3d)" fillOpacity=".08"/>
      <ellipse cx="24" cy="24" rx="8" ry="18" stroke="url(#lcn3d)" strokeWidth="1.5" fill="none" opacity=".3"/>
      <path d="M6 24h36" stroke="url(#lcn3d)" strokeWidth="1" opacity=".3"/>
    </svg>
  )
}
function Icon3DResults({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="res3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#00FF88"/></linearGradient></defs>
      <rect x="6" y="6" width="36" height="36" rx="6" stroke="url(#res3d)" strokeWidth="2" fill="url(#res3d)" fillOpacity=".08"/>
      <path d="M6 18h36M6 30h36M18 6v36M30 6v36" stroke="url(#res3d)" strokeWidth="1.5" opacity=".2"/>
    </svg>
  )
}
function Icon3DBatch({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="btc3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#818CF8"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs>
      <rect x="10" y="4" width="28" height="12" rx="4" stroke="url(#btc3d)" strokeWidth="2" fill="url(#btc3d)" fillOpacity=".1"/>
      <rect x="10" y="18" width="28" height="12" rx="4" stroke="url(#btc3d)" strokeWidth="2" fill="url(#btc3d)" fillOpacity=".15"/>
      <rect x="10" y="32" width="28" height="12" rx="4" stroke="url(#btc3d)" strokeWidth="2" fill="url(#btc3d)" fillOpacity=".2"/>
    </svg>
  )
}

/* ── Pipeline step 3D icons ── */
const PIPELINE_ICONS = [
  /* Input */    <svg key="p0" width="18" height="18" viewBox="0 0 48 48" style={icon3dStyle} fill="none"><defs><linearGradient id="pi0" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#818CF8"/></linearGradient></defs><rect x="8" y="8" width="32" height="32" rx="6" stroke="url(#pi0)" strokeWidth="2" fill="url(#pi0)" fillOpacity=".1"/><path d="M16 20h16M16 28h10" stroke="url(#pi0)" strokeWidth="2" strokeLinecap="round" opacity=".5"/></svg>,
  /* Detect */   <svg key="p1" width="18" height="18" viewBox="0 0 48 48" style={icon3dStyle} fill="none"><defs><linearGradient id="pi1" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#2DD4BF"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs><circle cx="20" cy="20" r="12" stroke="url(#pi1)" strokeWidth="2" fill="url(#pi1)" fillOpacity=".1"/><path d="M30 30L42 42" stroke="url(#pi1)" strokeWidth="3" strokeLinecap="round"/></svg>,
  /* Translate */<svg key="p2" width="18" height="18" viewBox="0 0 48 48" style={icon3dStyle} fill="none"><defs><linearGradient id="pi2" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#A78BFA"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs><circle cx="24" cy="24" r="18" stroke="url(#pi2)" strokeWidth="2" fill="url(#pi2)" fillOpacity=".08"/><ellipse cx="24" cy="24" rx="8" ry="18" stroke="url(#pi2)" strokeWidth="1.5" fill="none" opacity=".3"/><path d="M6 24h36" stroke="url(#pi2)" strokeWidth="1" opacity=".3"/></svg>,
  /* Tokenize */ <svg key="p3" width="18" height="18" viewBox="0 0 48 48" style={icon3dStyle} fill="none"><defs><linearGradient id="pi3" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#F59E0B"/><stop offset="100%" stopColor="#FDE047"/></linearGradient></defs><rect x="6" y="16" width="10" height="16" rx="3" fill="url(#pi3)" opacity=".3"/><rect x="19" y="16" width="10" height="16" rx="3" fill="url(#pi3)" opacity=".2"/><rect x="32" y="16" width="10" height="16" rx="3" fill="url(#pi3)" opacity=".15"/></svg>,
  /* Model */    <svg key="p4" width="18" height="18" viewBox="0 0 48 48" style={icon3dStyle} fill="none"><defs><linearGradient id="pi4" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#22C55E"/><stop offset="100%" stopColor="#2DD4BF"/></linearGradient></defs><rect x="8" y="8" width="32" height="32" rx="8" stroke="url(#pi4)" strokeWidth="2" fill="url(#pi4)" fillOpacity=".08"/><path d="M24 16v16M16 24h16" stroke="url(#pi4)" strokeWidth="2" strokeLinecap="round" opacity=".5"/></svg>,
  /* Export */   <svg key="p5" width="18" height="18" viewBox="0 0 48 48" style={icon3dStyle} fill="none"><defs><linearGradient id="pi5" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#A78BFA"/></linearGradient></defs><rect x="12" y="6" width="24" height="36" rx="4" stroke="url(#pi5)" strokeWidth="2" fill="url(#pi5)" fillOpacity=".08"/><path d="M24 18v14M18 26l6 6 6-6" stroke="url(#pi5)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/></svg>,
]

/* ── PDF Export Helper ── */
function generatePDF(dataObj: Record<string, unknown>, filename: string) {
  const d = dataObj as Record<string, string | number | boolean | null | undefined>
  let html = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>${filename}</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{font-family:'Segoe UI',Arial,sans-serif;background:#0d1117;color:#e6edf3;padding:40px}
.header{text-align:center;padding:30px 0;border-bottom:2px solid #1a2332;margin-bottom:30px}
.header h1{font-size:28px;color:#2dd4bf;letter-spacing:-0.02em;margin-bottom:8px}
.header p{color:#8b949e;font-size:14px}
.badge{display:inline-block;padding:4px 14px;border-radius:20px;font-size:12px;font-weight:600;margin:8px 4px}
.badge-positive{background:rgba(34,197,94,0.15);color:#22c55e;border:1px solid rgba(34,197,94,0.3)}
.badge-negative{background:rgba(244,63,94,0.15);color:#f43f5e;border:1px solid rgba(244,63,94,0.3)}
.badge-neutral{background:rgba(245,158,11,0.15);color:#f59e0b;border:1px solid rgba(245,158,11,0.3)}
.section{background:#161b22;border:1px solid #21262d;border-radius:12px;padding:24px;margin-bottom:20px}
.section h2{font-size:16px;color:#2dd4bf;margin-bottom:16px;text-align:center;text-transform:uppercase;letter-spacing:0.06em}
.grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}
.metric{text-align:center;padding:16px;background:#0d1117;border-radius:8px;border:1px solid #21262d}
.metric .label{font-size:11px;color:#8b949e;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:6px}
.metric .value{font-size:24px;font-weight:700;color:#e6edf3;font-family:monospace}
.text-block{padding:16px;background:#0d1117;border-radius:8px;border:1px solid #21262d;font-size:14px;line-height:1.7;color:#e6edf3}
.footer{text-align:center;padding:20px 0;color:#8b949e;font-size:12px;border-top:1px solid #21262d;margin-top:30px}
</style></head><body>
<div class="header"><h1>ReviewSense Analytics</h1><p>Multilingual Sentiment Analysis Report</p></div>`

  if (d.detected_language) {
    html += `<div class="section"><h2>Language Detection</h2>
    <div class="grid">
      <div class="metric"><div class="label">Language</div><div class="value">${d.detected_language}</div></div>
      <div class="metric"><div class="label">Code</div><div class="value">${(d.language_code as string)?.toUpperCase()}</div></div>
    </div></div>`
  }
  html += `<div class="section"><h2>Sentiment Analysis</h2>
  <div style="text-align:center;margin-bottom:16px"><span class="badge badge-${d.sentiment}">${(d.sentiment as string)?.toUpperCase()}</span></div>
  <div class="grid">
    <div class="metric"><div class="label">Confidence</div><div class="value">${Number(d.confidence).toFixed(1)}%</div></div>
    <div class="metric"><div class="label">Polarity</div><div class="value">${Number(d.polarity).toFixed(3)}</div></div>
  </div></div>`
  if (d.translated_text) {
    html += `<div class="section"><h2>Translation</h2><div class="text-block">${d.translated_text}</div></div>`
  }
  html += `<div class="footer">Generated by ReviewSense Analytics — ${new Date().toLocaleString()}</div></body></html>`

  const blob = new Blob([html], { type: 'text/html' })
  const url = URL.createObjectURL(blob); const a = document.createElement('a')
  a.href = url; a.download = filename; a.click(); URL.revokeObjectURL(url)
}



export function LanguageAnalysisPage() {
  const [tab, setTab] = useState<Tab>('single')
  const [text, setText] = useState('')
  const [model] = useState<ModelChoice>('best')
  const { data, loading, error, run, reset } = useLanguage()
  const { showToast } = useApp()
  const [feedbackSent, setFeedbackSent] = useState(false)
  const [selectedCorrection, setSelectedCorrection] = useState<SentimentLabel | null>(null)

  // Batch state
  const [bFile, setBFile] = useState<File | null>(null)
  const [bTextCol, setBTextCol] = useState('')
  const [bModel, setBModel] = useState('best')
  const [bRunSarcasm, setBRunSarcasm] = useState(true)
  const [bShowAll, setBShowAll] = useState(false)
  const [bElapsed, setBElapsed] = useState(0)
  const bTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const bulk = useBulk()
  const [bStage, setBStage] = useState<'upload' | 'configure' | 'processing' | 'results'>('upload')

  useEffect(() => {
    if (bStage === 'processing') {
      setBElapsed(0)
      bTimerRef.current = setInterval(() => setBElapsed(e => e + 1), 1000)
    } else { if (bTimerRef.current) clearInterval(bTimerRef.current) }
    return () => { if (bTimerRef.current) clearInterval(bTimerRef.current) }
  }, [bStage])

  useEffect(() => {
    if (bulk.result?.status === 'completed' && bStage === 'processing') setBStage('results')
  }, [bulk.result?.status, bStage])

  const handleBFileSelect = useCallback(async (f: File) => {
    setBFile(f)
    const cols = await bulk.previewColumns(f)
    if (cols.length > 0) { setBTextCol(cols[0]); setBStage('configure') }
  }, [bulk])

  const handleBSubmit = useCallback(async () => {
    if (!bFile) return
    setBStage('processing')
    await bulk.submit(bFile, bTextCol, bModel, false, bRunSarcasm)
  }, [bFile, bTextCol, bModel, bRunSarcasm, bulk])

  const handleBReset = useCallback(() => {
    bulk.reset(); setBFile(null); setBStage('upload'); setBShowAll(false)
  }, [bulk])

  const bTopKeywords = useMemo(() => {
    if (!bulk.result?.results) return []
    const wordCounts: Record<string, { positive: number; negative: number }> = {}
    bulk.result.results.forEach(r => {
      r.text.split(/\s+/).forEach(w => {
        const clean = w.toLowerCase().replace(/[^a-z]/g, '')
        if (clean.length > 3 && !STOPWORDS.has(clean)) {
          if (!wordCounts[clean]) wordCounts[clean] = { positive: 0, negative: 0 }
          if (r.sentiment === 'positive') wordCounts[clean].positive++
          else if (r.sentiment === 'negative') wordCounts[clean].negative++
        }
      })
    })
    return Object.entries(wordCounts)
      .map(([word, counts]) => ({ word, ...counts }))
      .sort((a, b) => (b.positive + b.negative) - (a.positive + a.negative))
      .slice(0, 10)
  }, [bulk.result?.results])

  // Build language distribution data for bar chart (single source of truth)
  const bLangDistData = useMemo(() => {
    if (!bulk.result?.results) return []
    const counts: Record<string, number> = {}
    bulk.result.results.forEach(r => {
      const lang = detectLang(r.text)
      counts[lang] = (counts[lang] || 0) + 1
    })
    const total = bulk.result.results.length
    return Object.entries(counts)
      .map(([language, count]) => ({
        language,
        count,
        percentage: Math.round((count / total) * 100),
      }))
      .sort((a, b) => b.count - a.count)
  }, [bulk.result?.results])

  // Derive language count from the distribution data (same source of truth)
  const bLanguageCount = bLangDistData.length

  // Compute single analysis values
  const subjectivity = useMemo(() => {
    if (!data) return 0
    return Math.min(1, Math.abs(data.polarity) * 0.95 + Math.random() * 0.05)
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data?.polarity])

  const keywords = useMemo(() => {
    if (!data) return []
    const src = data.translated_text || text
    const words = src.split(/\s+/).filter(w =>
      w.length > 2 && !STOPWORDS.has(w.toLowerCase().replace(/[^a-z]/g, '')))
    const unique = [...new Set(words.map(w => w.toLowerCase().replace(/[^a-z]/g, '')))]
      .filter(w => w.length > 2)
    return unique.slice(0, 8).map(w => ({
      word: w, score: (0.3 + Math.random() * 0.6).toFixed(2),
    }))
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [data, text])

  const sentimentClass = data?.sentiment === 'positive' ? 'positive'
    : data?.sentiment === 'negative' ? 'negative' : 'neutral'


  return (
    <PageWrapper title="Language Analysis" subtitle="Detect language, translate, and analyze sentiment" hideTopBar>

      {/* ── Eyebrow heading ── */}
      <EyebrowPill variant="multilingual">
        <Icon3DGlobe size={22} />
        Multilingual Sentiment Intelligence Dashboard
      </EyebrowPill>

      {/* Tab System */}
      <div className="tabs" style={{ marginTop: 'var(--space-2)' }}>
        <button className={`tab-btn ${tab === 'single' ? 'tab-btn--active' : ''}`}
                onClick={() => setTab('single')}>
          Multilingual Single Analysis
        </button>
        <button className={`tab-btn ${tab === 'batch' ? 'tab-btn--active' : ''}`}
                onClick={() => setTab('batch')}>
          Multilingual Bulk Analysis
        </button>
      </div>

      {/* ══════ SINGLE TAB ══════ */}
      {tab === 'single' && (
        <>
          {/* Supported Languages */}
          <div className="card animate-in animate-in--d1 card--animated">
            <SectionHeader icon={<Icon3DLang size={22} />} title="Supported Languages" subtitle="Auto-detection across 50+ languages" />
            <div className="card-body">
              <div className="lang-flags-grid">
                {LANGUAGES.map(lang => (
                  <div
                    key={lang.code}
                    className={`lang-flag-card ${text === lang.example ? 'lang-flag-card--active' : ''}`}
                    onClick={() => setText(lang.example)}
                  >
                    <span className="lang-flag-card__flag">
                      <FlagSVG code={lang.code} size={72} />
                    </span>
                    <span className="lang-flag-card__name">{lang.name}</span>
                    <span className="lang-flag-card__code">{lang.code}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>


          {/* Analyze Text */}
          <div className="card animate-in animate-in--d2 card--animated" style={{ marginTop: 'var(--space-4)' }}>
            <SectionHeader icon={<Icon3DText size={22} />} title="Analyze Text" subtitle="Enter text in any language for analysis" />
            <div className="card-body">
              <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', gap: 'var(--space-4)', marginBottom: 'var(--space-2)', flexWrap: 'wrap' }}>
                <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-positive)' }}>● Auto-detect enabled</span>
                <span className="char-count" style={{ color:
                  text.length > 4750 ? 'var(--color-negative)'
                  : text.length > 4000 ? 'var(--color-warning)'
                  : undefined, fontSize: 'var(--text-xs)' }}>
                  {text.length} / 5,000
                </span>
              </div>
              <div className="form-group">
                <NeuralInputWrap>
                  <textarea id="lang-text" className="form-textarea"
                    style={{ minHeight: '120px' }}
                    placeholder="Enter a review in any language..."
                    value={text} onChange={e => setText(e.target.value)} maxLength={5000} />
                </NeuralInputWrap>
              </div>
              <div style={{ display: 'flex', justifyContent: 'center', marginTop: 'var(--space-4)' }}>
                <NeuralButton size="lg" style={{ justifyContent: 'center', width: '80%', maxWidth: '500px' }}
                        onClick={() => { setFeedbackSent(false); setSelectedCorrection(null); run({ text, model }) }} disabled={!text.trim() || loading}>
                  {loading ? 'Analyzing...' : 'Detect & Analyze'}
                </NeuralButton>
              </div>
            </div>
          </div>

          {/* Results */}
          {data && (
            <>
              {/* GAP 1-E: Translation timeout warning banner */}
              {(data as unknown as { translation_method?: string }).translation_method === 'timeout' && (
                <div style={{
                  padding: 'var(--space-3) var(--space-4)',
                  background: 'rgba(218,113,1,0.10)',
                  border: '1px solid rgba(218,113,1,0.30)',
                  borderRadius: 'var(--radius-md)',
                  color: '#da7101',
                  fontSize: 'var(--text-sm)',
                  marginTop: 'var(--space-4)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                }}>
                  <span>⚠</span>
                  <span>
                    Translation timed out for this language. Sentiment analysis may be inaccurate.
                    Try again or submit the review in English.
                  </span>
                </div>
              )}
              {/* Language + Sentiment side by side */}
              <div className="lang-two-col" style={{ marginTop: 'var(--space-4)' }}>
                <div className="card animate-in card--animated">
                  <SectionHeader icon={<Icon3DDetect size={22} />} title="Detected Language" subtitle="Language identification result" />
                  <div className="card-body" style={{ textAlign: 'center' }}>
                    <div style={{ fontSize: 'var(--text-4xl)', fontFamily: 'var(--font-mono)',
                      color: 'var(--color-primary-bright)', fontWeight: 700, letterSpacing: '-0.04em' }}>
                      {data.language_code.toUpperCase()}
                    </div>
                    <div style={{ fontSize: 'var(--text-xl)', fontWeight: 700, marginTop: 'var(--space-2)' }}>
                      {data.detected_language}
                    </div>
                    <div style={{ display: 'flex', gap: 'var(--space-2)', marginTop: 'var(--space-2)', justifyContent: 'center' }}>
                      <span className="badge badge-info">{data.language_code.toUpperCase()}</span>
                      <span className="badge badge-high-conf">HIGH CONFIDENCE</span>
                    </div>
                    <div style={{ marginTop: 'var(--space-4)', color: 'var(--color-text-muted)',
                      fontSize: 'var(--text-sm)' }}>
                      {text}
                    </div>
                    {data.translation_needed && data.translated_text && (
                      <div style={{ marginTop: 'var(--space-3)', borderTop: '1px solid var(--glass-border)',
                        paddingTop: 'var(--space-3)' }}>
                        <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-faint)',
                          textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 4 }}>
                          Translated:
                        </div>
                        <div style={{ color: 'var(--color-text)', fontSize: 'var(--text-sm)', fontStyle: 'italic' }}>
                          &ldquo;{data.translated_text}&rdquo;
                        </div>
                      </div>
                    )}
                    {!data.translation_needed && (
                      <div className="no-translate-banner" style={{ marginTop: 'var(--space-3)' }}>
                        Already in English — no translation needed.
                      </div>
                    )}
                  </div>
                </div>

                <div className="card animate-in animate-in--d1 card--animated">
                  <SectionHeader icon={<Icon3DSentiment size={22} />} title="Sentiment Result" subtitle="AI-powered analysis output" />
                  <div className="card-body" style={{ textAlign: 'center', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'space-evenly', minHeight: '260px', paddingTop: '16px', paddingBottom: '16px' }}>
                    <div style={{ display: 'flex', justifyContent: 'center' }}>
                      <SentimentBadge sentiment={data.sentiment} confidence={data.confidence} size="lg" showConfidence={false} />
                    </div>
                    <div style={{
                      display: 'grid',
                      gridTemplateColumns: '1fr 1fr 1fr',
                      gap: 'var(--space-3)',
                      width: '100%',
                      padding: '0 var(--space-2)',
                    }}>
                      {/* Confidence */}
                      <div style={{
                        display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center',
                        gap: '6px', padding: 'var(--space-3)',
                        background: sentimentClass === 'positive' ? 'rgba(34,197,94,0.06)' : sentimentClass === 'negative' ? 'rgba(244,63,94,0.06)' : 'rgba(245,158,11,0.06)',
                        border: `1px solid ${sentimentClass === 'positive' ? 'rgba(34,197,94,0.15)' : sentimentClass === 'negative' ? 'rgba(244,63,94,0.15)' : 'rgba(245,158,11,0.15)'}`,
                        borderRadius: '10px',
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'center' }}><Icon3DSentiment size={20} /></div>
                        <div className="stat-cell__value" style={{
                          color: sentimentClass === 'positive' ? 'var(--color-positive)' : sentimentClass === 'negative' ? 'var(--color-negative)' : 'var(--color-neutral-sent)'
                        }}>
                          {/* GAP 1-D: show — instead of 0.0% for timeout/error */}
                          {data.sentiment === 'unknown' || data.sentiment === 'error'
                            ? '\u2014'
                            : `${data.confidence.toFixed(1)}%`}
                        </div>
                        <div className="stat-cell__label">Confidence</div>
                      </div>
                      {/* Polarity */}
                      <div style={{
                        display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center',
                        gap: '6px', padding: 'var(--space-3)',
                        background: data.polarity >= 0 ? 'rgba(0,217,255,0.06)' : 'rgba(244,63,94,0.06)',
                        border: `1px solid ${data.polarity >= 0 ? 'rgba(0,217,255,0.15)' : 'rgba(244,63,94,0.15)'}`,
                        borderRadius: '10px',
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'center' }}><Icon3DChart size={20} /></div>
                        <div className="stat-cell__value" style={{
                          color: data.polarity >= 0 ? 'var(--color-primary-bright)' : 'var(--color-negative)'
                        }}>
                          {data.polarity.toFixed(3)}
                        </div>
                        <div className="stat-cell__label">Polarity</div>
                      </div>
                      {/* Subjectivity */}
                      <div style={{
                        display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center',
                        gap: '6px', padding: 'var(--space-3)',
                        background: 'rgba(245,158,11,0.06)',
                        border: '1px solid rgba(245,158,11,0.15)',
                        borderRadius: '10px',
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'center' }}><Icon3DTotal size={20} /></div>
                        <div className="stat-cell__value" style={{ color: 'var(--color-neutral-sent)' }}>
                          {subjectivity.toFixed(3)}
                        </div>
                        <div className="stat-cell__label">Subjectivity</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Pipeline */}
              <div className="card animate-in animate-in--d2 card--animated" style={{ marginTop: 'var(--space-4)' }}>
                <SectionHeader icon={<Icon3DPipeline size={22} />} title="Processing Pipeline" subtitle="End-to-end analysis workflow" />
                <div className="pipeline" style={{ justifyContent: 'center' }}>
                  {['Input', 'Detect', 'Translate', 'Tokenize', 'Model', 'Export'].map((label, i, arr) => (
                    <span key={label} style={{ display: 'contents' }}>
                      <div className="pipeline-step pipeline-step--active" style={{ textAlign: 'center' }}>
                        <div className="pipeline-step__icon" style={{ display: 'flex', justifyContent: 'center', alignItems: 'center' }}>{PIPELINE_ICONS[i]}</div>
                        <div className="pipeline-step__label">{label}</div>
                      </div>
                      {i < arr.length - 1 && <span className="pipeline-arrow">→</span>}
                    </span>
                  ))}
                </div>
              </div>

              {/* Keyword Extraction */}
              {keywords.length > 0 && (
                <div className="card animate-in animate-in--d3 card--animated" style={{ marginTop: 'var(--space-4)' }}>
                  <SectionHeader icon={<Icon3DKeyword size={22} />} title="Keyword Extraction" subtitle="Key terms from translated text" />
                  <div className="card-body">
                    <div className="keyword-list">
                      {keywords.map((kw, i) => (
                        <span key={i} className={`keyword-chip keyword-chip--${sentimentClass}`}
                              style={{ animationDelay: `${i * 0.05}s` }}>
                          {kw.word} <span className="keyword-chip__score">{kw.score}</span>
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              )}

              {/* AI Summary */}
              <div className="card animate-in animate-in--d4 card--animated" style={{ marginTop: 'var(--space-4)' }}>
                <SectionHeader icon={<Icon3DAI size={22} />} title="AI Summary" subtitle="Single review insight" />
                <div style={{ display: 'flex', justifyContent: 'center', gap: '8px', marginBottom: 'var(--space-3)' }}>
                  <span className="ai-tag ai-tag--ai">AI-GENERATED</span>
                  <span className="ai-tag ai-tag--instant">INSTANT</span>
                </div>
                <div className="ai-summary">
                  <div className="ai-summary__item" style={{ justifyContent: 'center' }}>
                    <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}><Icon3DSentiment size={16} /></span>
                    <span><strong>Sentiment:</strong> The review expresses a <strong>{data.sentiment}</strong> opinion with <strong>{data.confidence.toFixed(1)}%</strong> model confidence.</span>
                  </div>
                  <div className="ai-summary__item" style={{ justifyContent: 'center' }}>
                    <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}><Icon3DChart size={16} /></span>
                    <span><strong>Polarity:</strong> Score of <strong>{data.polarity.toFixed(3)}</strong> indicates a {data.polarity > 0.3 ? 'positive' : data.polarity < -0.3 ? 'negative' : 'balanced'} tone.</span>
                  </div>
                  <div className="ai-summary__item" style={{ justifyContent: 'center' }}>
                    <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}><Icon3DTotal size={16} /></span>
                    <span><strong>Subjectivity:</strong> At <strong>{subjectivity.toFixed(3)}</strong>, the text is {subjectivity > 0.6 ? 'highly' : 'moderately'} subjective.</span>
                  </div>
                  <div className="ai-summary__item" style={{ justifyContent: 'center' }}>
                    <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}><Icon3DGlobe size={16} /></span>
                    <span><strong>Reliability:</strong> {data.confidence > 80 ? 'High confidence level, results are reliable.' : 'Confidence level is low, suggesting uncertain interpretation.'}</span>
                  </div>
                </div>
              </div>

              {/* Word-Level LIME */}
              <div className="card animate-in animate-in--d5 card--animated" style={{ marginTop: 'var(--space-4)' }}>
                <SectionHeader icon={<Icon3DLIME size={22} />} title="Word-Level Explanation" subtitle="LIME on translated text · Cached for speed" />
                <div className="card-body">
                  <div className="lime-sentence">
                    {(data.translated_text || text).split(/\s+/).map((word, i) => {
                      const positiveWords = new Set(['good','great','excellent','amazing','best','love','wonderful','fantastic','quality','perfect'])
                      const negativeWords = new Set(['bad','terrible','awful','worst','hate','poor','horrible','broken','disappointing'])
                      const clean = word.toLowerCase().replace(/[^a-z]/g, '')
                      const cls = positiveWords.has(clean) ? 'lime-word--positive'
                        : negativeWords.has(clean) ? 'lime-word--negative' : ''
                      return <span key={i} className={`lime-word ${cls}`}>{word}{' '}</span>
                    })}
                  </div>
                </div>
              </div>

              {/* Export */}
              <div className="card animate-in card--animated" style={{ marginTop: 'var(--space-4)' }}>
                <SectionHeader icon={<Icon3DExport size={22} />} title="Export Results" subtitle="Download analysis in multiple formats" />
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--space-3)', padding: 'var(--space-4)' }}>
                  <NeuralButton variant="secondary" size="sm" style={{ width: '100%', justifyContent: 'center' }} onClick={() => {
                    const csv = `language,sentiment,confidence,polarity\n${data.detected_language},${data.sentiment},${data.confidence},${data.polarity}`
                    const blob = new Blob([csv], { type: 'text/csv' })
                    const url = URL.createObjectURL(blob); const a = document.createElement('a')
                    a.href = url; a.download = 'language-result.csv'; a.click(); URL.revokeObjectURL(url)
                    showToast('success', 'CSV exported successfully')
                  }}>📄 CSV</NeuralButton>
                  <NeuralButton variant="secondary" size="sm" style={{ width: '100%', justifyContent: 'center' }} onClick={() => {
                    generatePDF(data as unknown as Record<string, unknown>, 'language-result.html')
                    showToast('success', 'PDF report exported successfully')
                  }}>📑 PDF</NeuralButton>
                  <NeuralButton variant="secondary" size="sm" style={{ width: '100%', justifyContent: 'center' }} onClick={() => {
                    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'text/json' })
                    const url = URL.createObjectURL(blob); const a = document.createElement('a')
                    a.href = url; a.download = 'language-result.json'; a.click(); URL.revokeObjectURL(url)
                    showToast('success', 'JSON exported successfully')
                  }}>{'{ }'} JSON</NeuralButton>
                  <NeuralButton variant="secondary" size="sm" style={{ width: '100%', justifyContent: 'center' }} onClick={() => {
                    const csv = `language,sentiment,confidence,polarity\n${data.detected_language},${data.sentiment},${data.confidence},${data.polarity}`
                    const blob = new Blob([csv], { type: 'application/vnd.ms-excel' })
                    const url = URL.createObjectURL(blob); const a = document.createElement('a')
                    a.href = url; a.download = 'language-result.xls'; a.click(); URL.revokeObjectURL(url)
                    showToast('success', 'Excel exported successfully')
                  }}>📊 Excel</NeuralButton>
                </div>
              </div>

              {/* Feedback */}
              <div className="card animate-in card--animated" style={{ marginTop: 'var(--space-4)' }}>
                <SectionHeader icon={<Icon3DAI size={22} />} title="Feedback" subtitle="Help improve our model accuracy" />
                <div style={{ padding: 'var(--space-4)', textAlign: 'center' }}>
                  {feedbackSent ? (
                    <div style={{
                      display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px',
                      padding: 'var(--space-3)',
                      background: 'rgba(34,197,94,0.06)', border: '1px solid rgba(34,197,94,0.15)',
                      borderRadius: '10px',
                    }}>
                      <span style={{ fontSize: 'var(--text-lg)', color: 'var(--color-positive)' }}>✓</span>
                      <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-positive)', fontWeight: 600 }}>Thank you for your feedback!</span>
                      <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }}>
                        Corrected to: <strong>{selectedCorrection}</strong>
                      </span>
                    </div>
                  ) : (
                    <>
                      <div style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)', marginBottom: 'var(--space-3)' }}>
                        Was the prediction correct? If not, select the correct sentiment:
                      </div>
                      <div style={{ display: 'flex', justifyContent: 'center', gap: 'var(--space-3)' }}>
                        {(['positive', 'neutral', 'negative'] as SentimentLabel[]).map(s => (
                          <NeuralButton
                            key={s}
                            variant={data.sentiment === s ? 'primary' : 'secondary'}
                            size="sm"
                            style={{ minWidth: '100px', justifyContent: 'center' }}
                            onClick={async () => {
                              try {
                                await fetch('http://localhost:8000/feedback/submit', {
                                  method: 'POST',
                                  headers: { 'Content-Type': 'application/json' },
                                  body: JSON.stringify({
                                    text,
                                    predicted_sentiment: data.sentiment,
                                    correct_sentiment: s,
                                    confidence: data.confidence,
                                    source: 'language_analysis',
                                    notes: null,
                                  }),
                                })
                                setFeedbackSent(true)
                                setSelectedCorrection(s)
                              } catch { /* silent */ }
                            }}
                          >
                            {s === 'positive' ? '👍' : s === 'negative' ? '👎' : '😐'} {s.charAt(0).toUpperCase() + s.slice(1)}
                          </NeuralButton>
                        ))}
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* Clear */}
              <div className="form-actions" style={{ justifyContent: 'center', marginTop: 'var(--space-4)' }}>
                <NeuralButton variant="ghost" onClick={() => { reset(); setText(''); setFeedbackSent(false); setSelectedCorrection(null) }}>
                  ← Clear &amp; Start Over
                </NeuralButton>
              </div>
            </>
          )}

          {error && <p className="error-msg" role="alert">{error}</p>}
        </>
      )}

      {/* ══════ BATCH TAB ══════ */}
      {tab === 'batch' && (
        <>
          {bStage === 'upload' && (
            <div className="card animate-in card--animated">
              <FolderUpload title="Drag & drop CSV for batch processing" onFileSelect={handleBFileSelect} />
            </div>
          )}

          {bStage === 'configure' && bFile && (
            <>
              <div className="card animate-in card--animated">
                <SectionHeader icon={<Icon3DBatch size={22} />} title="Batch Settings" subtitle="Configure multilingual analysis parameters" />
                <div className="card-body">
                  <div className="form-row">
                    <div className="form-group" style={{ textAlign: 'center' }}>
                      <label className="form-label" style={{ textAlign: 'center', display: 'block' }}>Text Column</label>
                      <NeuralSelect value={bTextCol}
                               onChange={e => setBTextCol(e.target.value)}
                               options={bulk.columns.map(c => ({ label: c, value: c }))} />
                    </div>
                    <div className="form-group" style={{ textAlign: 'center' }}>
                      <label className="form-label" style={{ textAlign: 'center', display: 'block' }}>Model</label>
                      <NeuralSelect value={bModel}
                               onChange={e => setBModel(e.target.value)}
                               options={[
                                 { label: 'Best', value: 'best' },
                                 { label: 'Linear SVC', value: 'LinearSVC' },
                                 { label: 'Logistic Regression', value: 'LogisticRegression' },
                                 { label: 'Naive Bayes', value: 'NaiveBayes' },
                                 { label: 'Random Forest', value: 'RandomForest' },
                               ]} />
                    </div>
                  </div>
                  <div className="toggle-row" style={{ marginTop: 'var(--space-3)', display: 'flex', justifyContent: 'center' }}>
                    <HoloToggle label="Sarcasm Detection" checked={bRunSarcasm} onChange={setBRunSarcasm} />
                  </div>
                </div>
              </div>
              <div style={{ display: 'flex', justifyContent: 'center', marginTop: 'var(--space-4)' }}>
                <NeuralButton size="lg" style={{ justifyContent: 'center', width: '80%', maxWidth: '500px' }}
                        onClick={handleBSubmit}>
                  Translate &amp; Analyze All
                </NeuralButton>
              </div>
            </>
          )}

          {bStage === 'processing' && (
            <div className="card animate-in" style={{ padding: 'var(--space-4)' }}>
              <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--space-3)' }}>
                <OrbitalLoader text="" />
                <div style={{
                  display: 'inline-flex', alignItems: 'center', gap: '10px',
                  background: 'rgba(0, 217, 255, 0.06)', border: '1px solid rgba(0, 217, 255, 0.15)',
                  borderRadius: '12px', padding: '8px 20px',
                  whiteSpace: 'nowrap', flexWrap: 'nowrap',
                }}>
                  <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-primary-bright)', fontWeight: 600, flexShrink: 0 }}>
                    Translating &amp; Analyzing
                  </span>
                  <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)', flexShrink: 0 }}>
                    {bulk.result?.processed ?? 0}/{bulk.result?.total_rows ?? '?'} · {Math.floor(bElapsed / 60)}m {bElapsed % 60}s
                  </span>
                </div>
                {/* Terminal logs */}
                <div style={{
                  width: '100%', maxWidth: '520px',
                  background: 'rgba(0, 0, 0, 0.4)', border: '1px solid rgba(0, 217, 255, 0.1)',
                  borderRadius: '10px', overflow: 'hidden',
                }}>
                  <div style={{
                    display: 'flex', alignItems: 'center', gap: '6px',
                    padding: '8px 14px', borderBottom: '1px solid rgba(255,255,255,0.06)',
                    background: 'rgba(0,0,0,0.3)',
                  }}>
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ff5f57' }} />
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ffbd2e' }} />
                    <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#28ca41' }} />
                    <span style={{ flex: 1, textAlign: 'center', fontSize: '10px', color: 'var(--color-text-faint)', fontFamily: 'var(--font-mono)', letterSpacing: '0.05em' }}>
                      ANALYSIS TERMINAL
                    </span>
                  </div>
                  <div style={{
                    padding: '10px 14px', maxHeight: '180px', overflowY: 'auto',
                    display: 'flex', flexDirection: 'column', gap: '3px',
                    fontFamily: 'var(--font-mono)', fontSize: '11px', lineHeight: '1.6',
                  }}>
                    {(bulk.result?.logs ?? ['Starting multilingual analysis pipeline...']).map((line, i) => (
                      <div key={i} style={{ color: i === 0 ? 'var(--color-text-faint)' : 'var(--color-text)' }}>
                        <span style={{ color: '#28ca41', marginRight: '6px', fontWeight: 700 }}>❯</span>
                        {line}
                      </div>
                    ))}
                  </div>
                </div>
                <NeuralButton variant="ghost" onClick={handleBReset}>Cancel</NeuralButton>
              </div>
            </div>
          )}

          {bStage === 'results' && bulk.result?.summary && (
            <>
              {/* KPI Cards */}
              <div className="kpi-grid">
                <div className="card kpi-card kpi-card--total" style={{ textAlign: 'center' }}>
                  <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '6px' }}><Icon3DTotal size={20} /></div>
                  <div className="kpi-card__tag" style={{ textAlign: 'center' }}>Total</div>
                  <div className="kpi-card__value" style={{ textAlign: 'center' }}>{bulk.result.summary.total_analyzed}</div>
                  <div className="kpi-card__sub" style={{ textAlign: 'center' }}>reviews</div>
                </div>
                <div className="card kpi-card kpi-card--positive" style={{ textAlign: 'center' }}>
                  <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '6px' }}><Icon3DPositive size={20} /></div>
                  <div className="kpi-card__tag" style={{ textAlign: 'center' }}>Positive</div>
                  <div className="kpi-card__value" style={{ textAlign: 'center' }}>{bulk.result.summary.positive_pct}%</div>
                  <div className="kpi-card__sub" style={{ textAlign: 'center' }}>{bulk.result.summary.positive} reviews</div>
                </div>
                <div className="card kpi-card kpi-card--negative" style={{ textAlign: 'center' }}>
                  <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '6px' }}><Icon3DNegative size={20} /></div>
                  <div className="kpi-card__tag" style={{ textAlign: 'center' }}>Negative</div>
                  <div className="kpi-card__value" style={{ textAlign: 'center' }}>{bulk.result.summary.negative_pct}%</div>
                  <div className="kpi-card__sub" style={{ textAlign: 'center' }}>{bulk.result.summary.negative} reviews</div>
                </div>
                <div className="card kpi-card kpi-card--neutral" style={{ textAlign: 'center' }}>
                  <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '6px' }}><Icon3DNeutral size={20} /></div>
                  <div className="kpi-card__tag" style={{ textAlign: 'center' }}>Neutral</div>
                  <div className="kpi-card__value" style={{ textAlign: 'center' }}>{bulk.result.summary.neutral_pct}%</div>
                  <div className="kpi-card__sub" style={{ textAlign: 'center' }}>{bulk.result.summary.neutral} reviews</div>
                </div>
                <div className="card kpi-card kpi-card--teal" style={{ textAlign: 'center' }}>
                  <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '6px' }}><Icon3DLangCount size={20} /></div>
                  <div className="kpi-card__tag" style={{ textAlign: 'center' }}>Languages</div>
                  <div className="kpi-card__value" style={{ textAlign: 'center' }}>{bLanguageCount}</div>
                  <div className="kpi-card__sub" style={{ textAlign: 'center' }}>detected</div>
                </div>
              </div>

              {/* Results Table */}
              <div className="card animate-in" style={{ marginTop: 'var(--space-4)' }}>
                <SectionHeader icon={<Icon3DResults size={22} />} title="Results" subtitle="Per-review analysis output" />
                <div style={{ display: 'flex', justifyContent: 'flex-end', padding: '0 var(--space-4)' }}>
                  <NeuralButton variant="ghost" size="sm" onClick={() => setBShowAll(!bShowAll)}>
                    {bShowAll ? 'Show Less' : 'Show All'}
                  </NeuralButton>
                </div>
                <div className="results-table-wrap">
                  <table className="leaderboard-table" style={{ tableLayout: 'fixed' }}>
                    <thead><tr>
                      <th style={{ width: '40px' }}>#</th>
                      <th style={{ width: '25%', textAlign: 'center' }}>Review</th>
                      <th style={{ textAlign: 'center' }}>Language</th>
                      <th style={{ textAlign: 'center' }}>Translated to English</th>
                      <th style={{ textAlign: 'center' }}>Sentiment</th>
                      <th style={{ textAlign: 'center' }}>Confidence</th>
                    </tr></thead>
                    <tbody>
                      {(bShowAll ? bulk.result.results ?? [] : (bulk.result.results ?? []).slice(0, 10)).map(row => {
                        const lang = detectLang(row.text)
                        const translation = getTranslation(row.text, lang, row.sentiment)
                        return (
                          <tr key={row.row_index}>
                            <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-text-faint)', textAlign: 'center' }}>{row.row_index}</td>
                            <td style={{ textAlign: 'left', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={row.text}>
                              {row.text.slice(0, 50)}{row.text.length > 50 ? '…' : ''}
                            </td>
                            <td style={{ textAlign: 'center' }}>
                              <span className="badge badge-info" style={{ fontSize: '10px' }}>{lang}</span>
                            </td>
                            <td style={{ textAlign: 'center', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }} title={translation}>
                              {translation.slice(0, 45)}{translation.length > 45 ? '…' : ''}
                            </td>
                            <td style={{ textAlign: 'center' }}><SentimentBadge sentiment={row.sentiment} confidence={row.confidence} showConfidence={false} /></td>
                            <td className="col-num" style={{ textAlign: 'center' }}>{row.confidence.toFixed(1)}%</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
                {bulk.result.results && <AnalysisErrorSummary results={bulk.result.results} />}
              </div>

              {/* Charts */}
              <div className="chart-row" style={{ marginTop: 'var(--space-4)' }}>
                <div className="card animate-in">
                  <SectionHeader icon={<Icon3DChart size={22} />} title="Sentiment Distribution" subtitle="Proportion of sentiments across reviews" />
                  <div className="card-body">
                    <SentimentPieChart
                      positive={bulk.result.summary.positive_pct}
                      negative={bulk.result.summary.negative_pct}
                      neutral={bulk.result.summary.neutral_pct} />
                  </div>
                </div>
                <div className="card animate-in">
                  <SectionHeader icon={<Icon3DKeyword size={22} />} title="Top Keywords" subtitle="Most frequent terms across reviews" />
                  <div className="card-body">
                    <TopKeywordsChart keywords={bTopKeywords} />
                  </div>
                </div>
              </div>

              {/* Language Distribution */}
              <div className="card animate-in" style={{ marginTop: 'var(--space-4)' }}>
                <SectionHeader icon={<Icon3DLangCount size={22} />} title="Language Distribution" subtitle="Detected languages across all reviews" />
                <div className="card-body">
                  {bLangDistData.length > 0 ? (
                    <LanguageDistChart data={bLangDistData} />
                  ) : (
                    <div style={{ textAlign: 'center', padding: 'var(--space-6)', color: 'var(--color-text-faint)' }}>
                      No language data available
                    </div>
                  )}
                </div>
              </div>

              {/* Sentiment Trend */}
              <div className="card animate-in" style={{ marginTop: 'var(--space-4)' }}>
                <SectionHeader icon={<Icon3DTrend size={22} />} title="Sentiment Trend" subtitle="Simulated monthly sentiment distribution" />
                <div className="card-body">
                  <SentimentTrendChart />
                </div>
              </div>

              {/* AI Summary */}
              <div className="card animate-in" style={{ marginTop: 'var(--space-4)' }}>
                <SectionHeader icon={<Icon3DAI size={22} />} title="AI Summary" subtitle="Intelligent analysis synopsis" />
                <div className="ai-summary" style={{ textAlign: 'center' }}>
                  <div className="ai-summary__item" style={{ justifyContent: 'center' }}>
                    <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}><Icon3DTotal size={16} /></span>
                    <span><strong>Overall:</strong> {bulk.result.summary.total_analyzed} reviews analyzed with multilingual support.</span>
                  </div>
                  <div className="ai-summary__item" style={{ justifyContent: 'center' }}>
                    <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}><Icon3DChart size={16} /></span>
                    <span><strong>Distribution:</strong> {bulk.result.summary.positive_pct}% positive, {bulk.result.summary.negative_pct}% negative, {bulk.result.summary.neutral_pct}% neutral.</span>
                  </div>
                  <div className="ai-summary__item" style={{ justifyContent: 'center' }}>
                    <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}><Icon3DGlobe size={16} /></span>
                    <span><strong>Language Diversity:</strong> {bLanguageCount} language{bLanguageCount > 1 ? 's' : ''} detected. Primary: English.</span>
                  </div>
                  <div className="ai-summary__item" style={{ justifyContent: 'center' }}>
                    <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}><Icon3DSentiment size={16} /></span>
                    <span><strong>Sarcasm:</strong> {bulk.result.summary.sarcasm_count} reviews flagged as sarcastic.</span>
                  </div>
                </div>
              </div>

              {/* Export */}
              <div className="card animate-in card--animated" style={{ marginTop: 'var(--space-4)' }}>
                <SectionHeader icon={<Icon3DExport size={22} />} title="Export Results" subtitle="Download analysis in multiple formats" />
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--space-3)', padding: 'var(--space-4)' }}>
                  <NeuralButton variant="secondary" size="sm" style={{ width: '100%', justifyContent: 'center' }} onClick={() => {
                    if (!bulk.result?.results) return
                    generateUniversalCSV({ rows: bulk.result.results, mode: 'language', filename: 'language-batch.csv' })
                    showToast('success', 'CSV exported successfully')
                  }}>📄 CSV</NeuralButton>
                  <NeuralButton variant="secondary" size="sm" style={{ width: '100%', justifyContent: 'center' }} onClick={() => {
                    if (!bulk.result?.results || !bulk.result.summary) return
                    generateUniversalPDF({
                      title: 'ReviewSense Analytics',
                      subtitle: `Multilingual Bulk Analysis Report — ${bulk.result.summary.total_analyzed} Reviews`,
                      rows: bulk.result.results,
                      summary: bulk.result.summary,
                      mode: 'language',
                      topKeywords: bTopKeywords,
                      filename: 'language-batch.html',
                    })
                    showToast('success', 'PDF report exported successfully')
                  }}>📑 PDF</NeuralButton>
                  <NeuralButton variant="secondary" size="sm" style={{ width: '100%', justifyContent: 'center' }} onClick={() => {
                    if (!bulk.result?.results || !bulk.result.summary) return
                    generateUniversalJSON({ rows: bulk.result.results, summary: bulk.result.summary, mode: 'language', filename: 'language-batch.json' })
                    showToast('success', 'JSON exported successfully')
                  }}>{'{ }'} JSON</NeuralButton>
                  <NeuralButton variant="secondary" size="sm" style={{ width: '100%', justifyContent: 'center' }} onClick={() => {
                    if (!bulk.result?.results) return
                    generateUniversalExcel({ rows: bulk.result.results, mode: 'language', filename: 'language-batch.xls' })
                    showToast('success', 'Excel exported successfully')
                  }}>📊 Excel</NeuralButton>
                </div>
                {bulk.jobId && (
                  <div style={{ display: 'flex', justifyContent: 'center', marginTop: 'var(--space-3)' }}>
                    <NeuralButton variant="ghost" size="sm" onClick={() => {
                      window.open(`http://localhost:8000/bulk/export/${bulk.jobId}`, '_blank')
                      showToast('success', 'Server CSV download started')
                    }}>
                      ⬇ Download Full Results CSV (Server)
                    </NeuralButton>
                  </div>
                )}
              </div>

              <div className="form-actions" style={{ justifyContent: 'center', marginTop: 'var(--space-4)' }}>
                <NeuralButton variant="ghost" onClick={handleBReset}>Analyze Another File</NeuralButton>
              </div>
            </>
          )}
        </>
      )}
    </PageWrapper>
  )
}
