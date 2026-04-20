import { useState, useCallback, useRef, useEffect, useMemo } from 'react'
import { SentimentBadge, AnalysisErrorSummary } from '@/components/ui/Badge'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { NeuralButton } from '@/components/ui/NeuralButton'
import { EyebrowPill } from '@/components/ui/EyebrowPill'
import { HoloToggle } from '@/components/ui/HoloToggle'
import { FolderUpload } from '@/components/ui/FolderUpload'
import { CyberLoader } from '@/components/ui/CyberLoader'
import { CyberCard } from '@/components/ui/CyberCard'
import { NeuralInputWrap } from '@/components/ui/NeuralInputWrap'
import { NeuralSelect } from '@/components/ui/NeuralSelect'
import { FlagSVG } from '@/components/ui/FlagSVG'
import { LIMEChart } from '@/components/charts/LIMEChart'
import { SentimentPieChart } from '@/components/charts/SentimentPieChart'
import { TopKeywordsChart } from '@/components/charts/TopKeywordsChart'
import { SentimentTrendChart } from '@/components/charts/SentimentTrendChart'
import { LanguageDistChart } from '@/components/charts/LanguageDistChart'
import { useLanguage } from '@/hooks/useLanguage'
import { useLanguageStore } from '@/hooks/useLanguageStore'
import { useBulk } from '@/hooks/useBulk'
import { useApp } from '@/context/AppContext'
import { pushTrendPoint, useTrendStore } from '@/hooks/useTrendStore'
import type { ModelChoice, DomainChoice, SentimentLabel } from '@/types/api.types'
import { generateUniversalPDF, generateUniversalCSV, generateUniversalExcel, generateUniversalJSON } from '@/utils/exportUtils'

const STOPWORDS = new Set(['a','the','is','was','and','or','but','in','on','at','it','this','that','to','of','for','with','be','are','have','i','my','me','we','they'])

/* ── Capitalize helper for Model & Domain labels ── */
function capitalize(s: string): string {
  if (s === 'all') return 'All'
  if (s === 'best') return 'Best'
  if (s === 'LinearSVC') return 'Linear SVC'
  return s
    .replace(/([a-z])([A-Z])/g, '$1 $2')
    .replace(/^./, c => c.toUpperCase())
    .trim()
}

const MODELS: ModelChoice[] = ['best','LinearSVC','LogisticRegression','NaiveBayes','RandomForest']
const DOMAINS: DomainChoice[] = ['all','food','ecom','movie','product']

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
function Icon3DFile({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="langfil3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00FF88"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs>
      <path d="M12 6h16l12 12v24a4 4 0 01-4 4H12a4 4 0 01-4-4V10a4 4 0 014-4z" stroke="url(#langfil3d)" strokeWidth="2" fill="url(#langfil3d)" fillOpacity=".1"/>
      <path d="M28 6v12h12" stroke="url(#langfil3d)" strokeWidth="2" strokeLinecap="round"/>
      <path d="M16 28h16M16 34h10" stroke="url(#langfil3d)" strokeWidth="1.5" strokeLinecap="round" opacity=".5"/>
    </svg>
  )
}
function Icon3DColumns({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="langcol3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#FDE047"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs>
      <rect x="6" y="8" width="12" height="32" rx="3" stroke="url(#langcol3d)" strokeWidth="2" fill="url(#langcol3d)" fillOpacity=".1"/>
      <rect x="22" y="8" width="12" height="32" rx="3" stroke="url(#langcol3d)" strokeWidth="2" fill="url(#langcol3d)" fillOpacity=".2"/>
      <rect x="38" y="8" width="4" height="32" rx="2" fill="url(#langcol3d)" opacity=".15"/>
    </svg>
  )
}
function Icon3DGearSettings({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="langgsz3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#A78BFA"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs>
      <path d="M24 16a8 8 0 100 16 8 8 0 000-16z" stroke="url(#langgsz3d)" strokeWidth="2" fill="url(#langgsz3d)" fillOpacity=".15"/>
      <path d="M24 4v6M24 38v6M4 24h6M38 24h6M9.9 9.9l4.2 4.2M33.9 33.9l4.2 4.2M38.1 9.9l-4.2 4.2M14.1 33.9l-4.2 4.2" stroke="url(#langgsz3d)" strokeWidth="2.5" strokeLinecap="round"/>
    </svg>
  )
}

function Icon3DPulse({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="lpls3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#2dd4bf"/></linearGradient></defs>
      <circle cx="24" cy="24" r="18" stroke="url(#lpls3d)" strokeWidth="1.5" fill="url(#lpls3d)" fillOpacity=".08" />
      <path d="M8 24h8l4-12 4 24 4-12 4 6 4-6h8" stroke="url(#lpls3d)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

function Icon3DGlobePanel({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="lglp3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#F43F5E"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs>
      <circle cx="24" cy="24" r="18" stroke="url(#lglp3d)" strokeWidth="2" fill="url(#lglp3d)" fillOpacity=".08" />
      <ellipse cx="24" cy="24" rx="10" ry="18" stroke="url(#lglp3d)" strokeWidth="1.5" fill="none" opacity=".4" />
      <path d="M6 24h36M8 14h32M8 34h32" stroke="url(#lglp3d)" strokeWidth="1.5" opacity=".25" />
    </svg>
  )
}

function Icon3DSentimentPie({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="lspie3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#22C55E"/><stop offset="100%" stopColor="#F59E0B"/></linearGradient></defs>
      <circle cx="24" cy="24" r="18" stroke="url(#lspie3d)" strokeWidth="2" fill="url(#lspie3d)" fillOpacity=".08" />
      <path d="M24 6v18l14 10" stroke="url(#lspie3d)" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M24 24L10 14" stroke="url(#lspie3d)" strokeWidth="1.5" strokeLinecap="round" opacity=".5" />
    </svg>
  )
}

function Icon3DGearPanel({ size = 16 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="lgp3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#A78BFA"/><stop offset="100%" stopColor="#818cf8"/></linearGradient></defs>
      <path d="M24 16a8 8 0 100 16 8 8 0 000-16z" stroke="url(#lgp3d)" strokeWidth="2" fill="url(#lgp3d)" fillOpacity=".15" />
      <path d="M24 4v6M24 38v6M4 24h6M38 24h6M9.9 9.9l4.2 4.2M33.9 33.9l4.2 4.2M38.1 9.9l-4.2 4.2M14.1 33.9l-4.2 4.2" stroke="url(#lgp3d)" strokeWidth="2" strokeLinecap="round" />
    </svg>
  )
}

/* ── 3D Tab Icons (same animation as sidebar nav-icon) ── */
function Icon3DTabSingle({ size = 20 }: { size?: number }) {
  return (
    <svg className="tab-icon-3d" width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="tabSng3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#00D9FF"/><stop offset="100%" stopColor="#2DD4BF"/></linearGradient></defs>
      <rect x="6" y="10" width="36" height="28" rx="6" stroke="url(#tabSng3d)" strokeWidth="2" fill="url(#tabSng3d)" fillOpacity=".08"/>
      <path d="M14 20h20M14 26h16M14 32h12" stroke="url(#tabSng3d)" strokeWidth="2" strokeLinecap="round" opacity=".5"/>
      <circle cx="38" cy="12" r="6" fill="url(#tabSng3d)" opacity=".25"/>
      <path d="M36 12l2 2 3-4" stroke="url(#tabSng3d)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" opacity=".7"/>
    </svg>
  )
}
function Icon3DTabBulk({ size = 20 }: { size?: number }) {
  return (
    <svg className="tab-icon-3d" width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="tabBlk3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#A78BFA"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs>
      <rect x="4" y="14" width="28" height="24" rx="5" stroke="url(#tabBlk3d)" strokeWidth="2" fill="url(#tabBlk3d)" fillOpacity=".08"/>
      <rect x="10" y="8" width="28" height="24" rx="5" stroke="url(#tabBlk3d)" strokeWidth="2" fill="url(#tabBlk3d)" fillOpacity=".06"/>
      <rect x="16" y="2" width="28" height="24" rx="5" stroke="url(#tabBlk3d)" strokeWidth="2" fill="url(#tabBlk3d)" fillOpacity=".04"/>
      <path d="M22 10h16M22 16h12" stroke="url(#tabBlk3d)" strokeWidth="1.5" strokeLinecap="round" opacity=".35"/>
    </svg>
  )
}

function Icon3DTarget({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="tgt3dL" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#F59E0B"/><stop offset="100%" stopColor="#00D9FF"/></linearGradient></defs>
      <circle cx="24" cy="24" r="18" stroke="url(#tgt3dL)" strokeWidth="2" fill="url(#tgt3dL)" fillOpacity=".06"/>
      <circle cx="24" cy="24" r="10" stroke="url(#tgt3dL)" strokeWidth="1.5" fill="none" opacity=".4"/>
      <circle cx="24" cy="24" r="4" fill="url(#tgt3dL)" opacity=".8"/>
    </svg>
  )
}

function Icon3DSarcasm({ size = 22 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 48 48" style={icon3dStyle} fill="none">
      <defs><linearGradient id="sarcL3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#F43F5E"/><stop offset="100%" stopColor="#A78BFA"/></linearGradient></defs>
      <path d="M24 4L6 14v12c0 12 8 16 18 18 10-2 18-6 18-18V14L24 4z" stroke="url(#sarcL3d)" strokeWidth="2" fill="url(#sarcL3d)" fillOpacity=".1"/>
      <path d="M24 18v8M24 31v2" stroke="url(#sarcL3d)" strokeWidth="2.5" strokeLinecap="round"/>
    </svg>
  )
}

function PanelBadge({ icon, label, bg, border, color }: {
  icon: React.ReactNode, label: string,
  bg: string, border: string, color: string,
}) {
  return (
    <div style={{
      display: 'inline-flex', alignItems: 'center', gap: '7px', alignSelf: 'center',
      background: bg, border: `1px solid ${border}`,
      borderRadius: '10px', padding: '5px 14px',
      marginBottom: '10px',
    }}>
      {icon}
      <span style={{
        fontSize: '10px', fontWeight: 700,
        textTransform: 'uppercase', letterSpacing: '0.08em',
        color,
      }}>{label}</span>
    </div>
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
function generatePDF(dataObj: Record<string, unknown>, keywords: Array<{word: string, score: string}>, filename: string) {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const d = dataObj as any
  const sentiment = (d.sentiment as string) ?? 'neutral'
  const confidence = Number(d.confidence ?? 0)
  const polarity   = Number(d.polarity   ?? 0)
  const badgeColor = sentiment === 'positive' ? '#22c55e' : sentiment === 'negative' ? '#f43f5e' : '#f59e0b'
  const polarityColor = polarity >= 0 ? '#00D9FF' : '#f43f5e'
  const polarityPct   = Math.min(100, Math.abs(polarity) * 100)
  const subjectivity = Math.min(1, Math.abs(polarity) * 0.95 + 0.02)

  const absaRows = d.absa && d.absa.length > 0
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ? d.absa.map((a: any) => {
        const c = a.sentiment === 'positive' ? '#22c55e' : a.sentiment === 'negative' ? '#f43f5e' : '#f59e0b'
        return `<tr><td style="font-weight:600;color:#2dd4bf">${a.aspect}</td><td><span style="display:inline-block;padding:2px 10px;border-radius:10px;font-size:10px;font-weight:700;background:${c}22;color:${c};border:1px solid ${c}55">${a.sentiment.toUpperCase()}</span></td><td style="font-family:monospace">${Number(a.polarity).toFixed(3)}</td></tr>`
      }).join('')
    : ''

  const limeRows = d.lime_features && d.lime_features.length > 0
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    ? d.lime_features.map((f: any) => {
        const w = f.weight
        const c = w > 0 ? '#22c55e' : '#f43f5e'
        const barW = Math.min(100, Math.abs(w) * 200)
        const leftBar = w < 0 ? '<div style="height:10px;width:' + barW + '%;background:' + c + ';border-radius:4px 0 0 4px"></div>' : ''
        const rightBar = w > 0 ? '<div style="height:10px;width:' + barW + '%;background:' + c + ';border-radius:0 4px 4px 0"></div>' : ''
        return `<tr><td style="font-weight:600">${f.word}</td><td style="font-family:monospace;color:${c}">${w > 0 ? '+' : ''}${Number(w).toFixed(4)}</td><td><div style="display:flex;width:100%;align-items:center"><div style="flex:1;display:flex;justify-content:flex-end;padding-right:2px">${leftBar}</div><div style="width:2px;height:14px;background:#30363d"></div><div style="flex:1;display:flex;justify-content:flex-start;padding-left:2px">${rightBar}</div></div></td></tr>`
      }).join('')
    : ''

  const kwBadges = keywords && keywords.length > 0
    ? `<div style="display:flex;flex-wrap:wrap;justify-content:center;gap:10px;padding:10px 0">${keywords.map(kw => `<span style="background:rgba(0,217,255,0.1);color:#00D9FF;border:1px solid rgba(0,217,255,0.25);padding:4px 12px;border-radius:16px;font-size:12px;font-weight:600">${kw.word} <span style="opacity:0.6;font-family:monospace;margin-left:4px">${kw.score}</span></span>`).join('')}</div>`
    : ''

  // ── Inline logo (favicon SVG scaled to 64px) ──────────────────────────────
  const LOGO = `<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 48 48" fill="none">
    <defs>
      <radialGradient id="lc" cx="50%" cy="50%" r="50%">
        <stop offset="0%" stop-color="#ffffff" stop-opacity="1"/>
        <stop offset="20%" stop-color="#aaf8ff" stop-opacity="0.95"/>
        <stop offset="45%" stop-color="#00d9ff" stop-opacity="0.65"/>
        <stop offset="72%" stop-color="#0055aa" stop-opacity="0.20"/>
        <stop offset="100%" stop-color="#001133" stop-opacity="0"/>
      </radialGradient>
      <filter id="lg" x="-30%" y="-30%" width="160%" height="160%">
        <feGaussianBlur stdDeviation="1.0" result="b"/>
        <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
      </filter>
    </defs>
    <circle cx="24" cy="24" r="22" stroke="#00ccff" stroke-width="2.8" stroke-linecap="round" stroke-dasharray="14 4.2" stroke-opacity="0.72" fill="none" filter="url(#lg)"/>
    <circle cx="24" cy="24" r="20" stroke="#0088dd" stroke-width="0.9" stroke-linecap="square" stroke-dasharray="6 1 2 1 3 2" stroke-opacity="0.42" fill="none"/>
    <circle cx="24" cy="24" r="17.5" stroke="#00bbee" stroke-width="2.0" stroke-linecap="round" stroke-dasharray="10 3 4 3" stroke-opacity="0.68" fill="none" filter="url(#lg)"/>
    <circle cx="24" cy="24" r="13.5" stroke="#00ddff" stroke-width="1.6" stroke-linecap="round" stroke-dasharray="8 3" stroke-opacity="0.62" fill="none" filter="url(#lg)"/>
    <circle cx="24" cy="24" r="10.5" stroke="#55eeff" stroke-width="1.0" stroke-linecap="round" stroke-dasharray="5 2.5" stroke-opacity="0.55" fill="none" filter="url(#lg)"/>
    <circle cx="24" cy="24" r="7.0" stroke="#00eeff" stroke-width="0.8" stroke-dasharray="2.5 2" stroke-opacity="0.60" fill="none"/>
    <circle cx="24" cy="24" r="6.5" fill="url(#lc)"/>
  </svg>`

  // ── 3D Section icons ──────────────────────────────────────────────────────
  const I = {
    sentiment:  `<svg width="22" height="22" viewBox="0 0 48 48" fill="none" style="vertical-align:middle"><defs><linearGradient id="pi1" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#22C55E"/><stop offset="100%" stop-color="#00FF88"/></linearGradient></defs><circle cx="24" cy="24" r="18" stroke="url(#pi1)" stroke-width="2" fill="url(#pi1)" fill-opacity=".1"/><path d="M16 28c2 4 5 6 8 6s6-2 8-6" stroke="url(#pi1)" stroke-width="2" stroke-linecap="round"/><circle cx="18" cy="20" r="2" fill="url(#pi1)"/><circle cx="30" cy="20" r="2" fill="url(#pi1)"/></svg>`,
    confidence: `<svg width="22" height="22" viewBox="0 0 48 48" fill="none" style="vertical-align:middle"><defs><linearGradient id="pi2" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#00D9FF"/><stop offset="100%" stop-color="#A78BFA"/></linearGradient></defs><rect x="6" y="6" width="36" height="36" rx="6" stroke="url(#pi2)" stroke-width="2" fill="url(#pi2)" fill-opacity=".08"/><path d="M14 36V24M22 36V18M30 36V28M38 36V12" stroke="url(#pi2)" stroke-width="2.5" stroke-linecap="round"/></svg>`,
    polarity:   `<svg width="22" height="22" viewBox="0 0 48 48" fill="none" style="vertical-align:middle"><defs><linearGradient id="pi3" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#A78BFA"/><stop offset="100%" stop-color="#00D9FF"/></linearGradient></defs><path d="M24 8L40 38H8z" stroke="url(#pi3)" stroke-width="2" fill="url(#pi3)" fill-opacity=".15" stroke-linejoin="round"/><path d="M24 18v10M24 32v2" stroke="url(#pi3)" stroke-width="2" stroke-linecap="round"/></svg>`,
    subjectivity:`<svg width="22" height="22" viewBox="0 0 48 48" fill="none" style="vertical-align:middle"><defs><linearGradient id="pi4" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#FDE047"/><stop offset="100%" stop-color="#F59E0B"/></linearGradient></defs><circle cx="24" cy="24" r="16" stroke="url(#pi4)" stroke-width="2" fill="none"/><circle cx="24" cy="24" r="8" stroke="url(#pi4)" stroke-width="1.5" fill="url(#pi4)" fill-opacity=".15"/><circle cx="24" cy="24" r="3" fill="url(#pi4)"/></svg>`,
    gauge:      `<svg width="22" height="22" viewBox="0 0 48 48" fill="none" style="vertical-align:middle"><defs><linearGradient id="pi5" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#00D9FF"/><stop offset="100%" stop-color="#00FF88"/></linearGradient></defs><path d="M8 36a16 16 0 1 1 32 0" stroke="url(#pi5)" stroke-width="3" stroke-linecap="round" fill="none"/><path d="M24 36L24 22" stroke="url(#pi5)" stroke-width="2.5" stroke-linecap="round"/><circle cx="24" cy="36" r="3" fill="url(#pi5)"/></svg>`,
    details:    `<svg width="22" height="22" viewBox="0 0 48 48" fill="none" style="vertical-align:middle"><defs><linearGradient id="pi6" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#00D9FF"/><stop offset="100%" stop-color="#A78BFA"/></linearGradient></defs><rect x="8" y="6" width="32" height="36" rx="4" stroke="url(#pi6)" stroke-width="2" fill="url(#pi6)" fill-opacity=".1"/><path d="M14 18h20M14 26h16M14 34h12" stroke="url(#pi6)" stroke-width="2" stroke-linecap="round" opacity=".7"/></svg>`,
    ai:         `<svg width="22" height="22" viewBox="0 0 48 48" fill="none" style="vertical-align:middle"><defs><linearGradient id="pi7" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#A78BFA"/><stop offset="100%" stop-color="#00D9FF"/></linearGradient></defs><rect x="10" y="14" width="28" height="24" rx="6" stroke="url(#pi7)" stroke-width="2" fill="url(#pi7)" fill-opacity=".12"/><circle cx="19" cy="26" r="3" fill="url(#pi7)" opacity=".7"/><circle cx="29" cy="26" r="3" fill="url(#pi7)" opacity=".7"/><path d="M20 33h8" stroke="url(#pi7)" stroke-width="2" stroke-linecap="round"/><path d="M24 14V8M18 8h12" stroke="url(#pi7)" stroke-width="2" stroke-linecap="round"/></svg>`,
    absa:       `<svg width="22" height="22" viewBox="0 0 48 48" fill="none" style="vertical-align:middle"><defs><linearGradient id="pi8" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#F59E0B"/><stop offset="100%" stop-color="#00D9FF"/></linearGradient></defs><circle cx="24" cy="24" r="18" stroke="url(#pi8)" stroke-width="2" fill="url(#pi8)" fill-opacity=".06"/><circle cx="24" cy="24" r="10" stroke="url(#pi8)" stroke-width="1.5" fill="none" opacity=".4"/><circle cx="24" cy="24" r="4" fill="url(#pi8)" opacity=".8"/></svg>`,
    lime:       `<svg width="22" height="22" viewBox="0 0 48 48" fill="none" style="vertical-align:middle"><defs><linearGradient id="pi9" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#22C55E"/><stop offset="100%" stop-color="#A78BFA"/></linearGradient></defs><path d="M6 38l10-14 8 6 8-12 10-8" stroke="url(#pi9)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" fill="none"/><circle cx="42" cy="10" r="3" fill="url(#pi9)"/></svg>`,
    sarcasm:    `<svg width="22" height="22" viewBox="0 0 48 48" fill="none" style="vertical-align:middle"><defs><linearGradient id="pi10" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#F43F5E"/><stop offset="100%" stop-color="#A78BFA"/></linearGradient></defs><path d="M24 4L6 14v12c0 12 8 16 18 18 10-2 18-6 18-18V14L24 4z" stroke="url(#pi10)" stroke-width="2" fill="url(#pi10)" fill-opacity=".1"/><path d="M24 18v8M24 31v2" stroke="url(#pi10)" stroke-width="2.5" stroke-linecap="round"/></svg>`,
    lang:       `<svg width="22" height="22" viewBox="0 0 48 48" fill="none" style="vertical-align:middle"><defs><linearGradient id="pi11" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#A78BFA"/><stop offset="100%" stop-color="#00D9FF"/></linearGradient></defs><circle cx="24" cy="24" r="20" stroke="url(#pi11)" stroke-width="2" fill="url(#pi11)" fill-opacity=".08"/><ellipse cx="24" cy="24" rx="10" ry="20" stroke="url(#pi11)" stroke-width="1.5" fill="none" opacity=".4"/><path d="M4 24h40" stroke="url(#pi11)" stroke-width="1" opacity=".3"/></svg>`,
    input:      `<svg width="22" height="22" viewBox="0 0 48 48" fill="none" style="vertical-align:middle"><defs><linearGradient id="pi12" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#00D9FF"/><stop offset="100%" stop-color="#A78BFA"/></linearGradient></defs><rect x="6" y="6" width="36" height="36" rx="6" stroke="url(#pi12)" stroke-width="2" fill="url(#pi12)" fill-opacity=".08"/><path d="M14 18h20M14 26h16M14 34h12" stroke="url(#pi12)" stroke-width="2" stroke-linecap="round" opacity=".6"/></svg>`,
    transl:     `<svg width="22" height="22" viewBox="0 0 48 48" fill="none" style="vertical-align:middle"><defs><linearGradient id="pi13" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#2DD4BF"/><stop offset="100%" stop-color="#00D9FF"/></linearGradient></defs><path d="M6 12h20M16 8v4M10 16c1 4 6 8 10 8M16 24c4-2 8-4 10-8" stroke="url(#pi13)" stroke-width="2" stroke-linecap="round" fill="none"/><path d="M28 28l6-12 6 12M30 36h8" stroke="url(#pi13)" stroke-width="2" stroke-linecap="round"/></svg>`,
    key:        `<svg width="22" height="22" viewBox="0 0 48 48" fill="none" style="vertical-align:middle"><defs><linearGradient id="piKey" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stop-color="#F59E0B"/><stop offset="100%" stop-color="#FDE047"/></linearGradient></defs><circle cx="34" cy="14" r="8" stroke="url(#piKey)" stroke-width="2" fill="url(#piKey)" fill-opacity=".15"/><circle cx="34" cy="14" r="2" fill="url(#piKey)"/><path d="M28 20L6 42v-6l4-4v-4l4-4v-4l10-10" stroke="url(#piKey)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
  }

  const iconHead = (icon: string, label: string) =>
    `<div class="section-head"><div class="section-head-box">${icon}<h2>${label}</h2></div></div>`

  let html = `<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><title>${filename}</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
@page{size:A4;margin:0}
html,body{width:100%;min-height:100vh}
body{font-family:'Segoe UI',Arial,sans-serif;background:#0d1117;color:#e6edf3;padding:36px 40px;width:100%}
.header{text-align:center;padding:36px 0 28px;border-bottom:2px solid rgba(45,212,191,0.25);margin-bottom:30px}
.header h1{font-size:34px;color:#2dd4bf;letter-spacing:-0.02em;margin-bottom:8px;font-weight:800}
.header p{color:#8b949e;font-size:14px;margin-bottom:10px}
.header .tag{display:inline-block;padding:5px 16px;border-radius:20px;font-size:11px;font-weight:700;background:rgba(45,212,191,0.1);color:#2dd4bf;border:1px solid rgba(45,212,191,0.25);letter-spacing:.1em;text-transform:uppercase}
.section{background:#161b22;border:1px solid #21262d;border-radius:16px;padding:24px 28px;margin-bottom:22px}
.section-head{display:flex;align-items:center;justify-content:center;gap:0;margin-bottom:18px}
.section-head h2{font-size:14px;color:#2dd4bf;text-transform:uppercase;letter-spacing:.1em;font-weight:700;margin:0}
.section-head-box{display:inline-flex;align-items:center;gap:10px;background:rgba(13,17,23,0.8);border:1px solid rgba(45,212,191,0.22);border-radius:14px;padding:8px 22px;box-shadow:0 0 16px rgba(0,217,255,0.08)}
.kpis{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:26px}
.kpi{text-align:center;padding:20px 16px;background:#161b22;border-radius:14px;border:1px solid #21262d}
.kpi .value{font-size:26px;font-weight:800;font-family:'Courier New',monospace}
.analytics-grid{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin-bottom:22px}
.a-card{background:#0f1419;border:1px solid #2a3441;border-radius:16px;padding:22px 24px}
table{width:100%;border-collapse:collapse;font-size:12px}
th{padding:10px;text-align:center;font-size:10px;text-transform:uppercase;letter-spacing:.07em;color:#8b949e;border-bottom:2px solid #21262d;background:#0d1117}
td{padding:9px 10px;text-align:center;border-bottom:1px solid rgba(33,38,45,.6);color:#e6edf3;vertical-align:middle}
.text-box{background:#0d1117;border:1px solid #21262d;border-radius:10px;padding:16px;font-size:14px;line-height:1.8;color:#e6edf3;text-align:center}
.gauge-track{background:#21262d;border-radius:8px;height:20px;overflow:hidden;margin:10px 0}
.ai-item{display:flex;align-items:flex-start;gap:10px;padding:9px 0;border-bottom:1px solid rgba(255,255,255,.06);font-size:12px;line-height:1.7;justify-content:flex-start;text-align:left;width:100%}
.ai-item:last-child{border-bottom:none}
.footer{text-align:center;padding:22px 0;color:#8b949e;font-size:11px;border-top:1px solid #21262d;margin-top:26px}
.footer .brand{color:#2dd4bf;font-weight:700;font-size:12px}
</style></head><body>

<div class="header">
  <div style="display:flex;justify-content:center;margin-bottom:14px">${LOGO}</div>
  <h1 style="color:#2dd4bf;margin-bottom:8px">ReviewSense Analytics</h1>
  <div class="section-head" style="margin-top:16px;margin-bottom:16px"><div class="section-head-box"><h2 style="font-size:14px">Multilingual Sentiment Analysis Report</h2></div></div>
  <span class="tag">AI-POWERED &middot; ${new Date().toLocaleDateString()}</span>
</div>

<div class="kpis">
  <div class="kpi"><div class="section-head" style="margin-bottom:12px"><div class="section-head-box">${I.sentiment}<h2>Sentiment</h2></div></div><div class="value" style="color:${badgeColor};font-size:18px">${sentiment.toUpperCase()}</div></div>
  <div class="kpi"><div class="section-head" style="margin-bottom:12px"><div class="section-head-box">${I.confidence}<h2>Confidence</h2></div></div><div class="value" style="color:#00D9FF">${confidence.toFixed(1)}%</div></div>
  <div class="kpi"><div class="section-head" style="margin-bottom:12px"><div class="section-head-box">${I.polarity}<h2>Polarity</h2></div></div><div class="value" style="color:${polarityColor}">${polarity.toFixed(3)}</div></div>
  <div class="kpi"><div class="section-head" style="margin-bottom:12px"><div class="section-head-box">${I.lang}<h2>Language</h2></div></div><div class="value" style="color:#A78BFA;font-size:16px">${d.detected_language ?? 'English'}</div></div>
</div>
`

  if (d.original_text || d.text) {
    html += `<div class="section">${iconHead(I.input,'Input Review')}
  <div class="text-box">${String(d.original_text ?? d.text ?? '').replace(/</g,'&lt;').replace(/>/g,'&gt;')}</div>
</div>`
  }

  if (d.detected_language) {
    html += `<div class="analytics-grid">
  <div class="a-card">
    ${iconHead(I.lang, 'Language Detection')}
    <div style="text-align:center;font-size:13px;line-height:2">
      <div>Language: <strong style="color:#A78BFA">${d.detected_language}</strong></div>
      <div>Code: <strong>${String(d.language_code ?? '').toUpperCase()}</strong></div>
    </div>
  </div>
  <div class="a-card">
    ${iconHead(I.gauge, 'Polarity Gauge')}
    <div style="text-align:center;padding:4px 0">
      <div class="gauge-track"><div style="width:${polarityPct}%;height:100%;background:${polarityColor};border-radius:8px"></div></div>
      <div style="font-size:13px;color:${polarityColor};font-weight:700;margin-top:8px">${polarity >= 0 ? 'Positive' : 'Negative'} Tone &middot; ${polarity.toFixed(3)}</div>
    </div>
  </div>
</div>`
  }

  if (d.translated_text) {
    html += `<div class="section">${iconHead(I.transl,'Translation to English')}
  <div class="text-box">${String(d.translated_text).replace(/</g,'&lt;').replace(/>/g,'&gt;')}</div>
</div>`
  }

  if (kwBadges) {
    html += `<div class="section">${iconHead(I.key,'Keyword Extraction')}
  ${kwBadges}
</div>`
  }

  html += `<div class="section">${iconHead(I.ai,'AI Summary')}
  <div class="ai-item"><span>&#129504;</span><span><strong>Sentiment:</strong> The review expresses a <strong>${sentiment}</strong> opinion with <strong>${confidence.toFixed(1)}%</strong> model confidence.</span></div>
  <div class="ai-item"><span>&#9651;</span><span><strong>Polarity:</strong> Score of <strong>${polarity.toFixed(3)}</strong> indicates a ${polarity > 0.3 ? 'positive' : polarity < -0.3 ? 'negative' : 'balanced'} tone.</span></div>
  <div class="ai-item"><span>&#9678;</span><span><strong>Subjectivity:</strong> At <strong>${subjectivity.toFixed(3)}</strong>, the text is ${subjectivity > 0.6 ? 'highly' : 'moderately'} subjective.</span></div>
  ${d.detected_language ? `<div class="ai-item"><span>&#127760;</span><span><strong>Language:</strong> Detected as <strong>${d.detected_language}</strong>. Translation provided for analysis.</span></div>` : ''}
</div>`

  if (absaRows) {
    html += `<div class="section">${iconHead(I.absa,'Aspect-Based Sentiment Analysis')}
  <table><thead><tr><th>Aspect</th><th>Sentiment</th><th>Polarity</th></tr></thead>
  <tbody>${absaRows}</tbody></table>
</div>`
  }

  if (limeRows) {
    html += `<div class="section">${iconHead(I.lime,'LIME Feature Contributions')}
  <table><thead><tr><th>Word</th><th>Weight</th><th>Contribution</th></tr></thead>
  <tbody>${limeRows}</tbody></table>
</div>`
  }

  if (d.sarcasm) {
    html += `<div class="section" style="text-align:center">${iconHead(I.sarcasm,'Sarcasm Detection')}
  <div style="display:inline-block;padding:14px 28px;background:${d.sarcasm.detected ? 'rgba(244,63,94,0.08)' : 'rgba(34,197,94,0.08)'};border:1px solid ${d.sarcasm.detected ? 'rgba(244,63,94,0.25)' : 'rgba(34,197,94,0.2)'};border-radius:12px;margin:4px 0;text-align:center">
    <div style="font-size:16px;font-weight:700;color:${d.sarcasm.detected ? '#f43f5e' : '#22c55e'};margin-bottom:6px">${d.sarcasm.detected ? '\u26a0\ufe0f Sarcasm Detected' : '\u2705 No Sarcasm Detected'}</div>
    <div style="font-size:12px;color:#8b949e;text-align:center">${d.sarcasm.detected ? 'This review may contain ironic or sarcastic language.' : 'The model found no indicators of sarcasm.'}</div>
  </div>
</div>`
  }

  html += `<div class="footer"><span class="brand">ReviewSense Analytics</span> &mdash; Generated ${new Date().toLocaleString()}</div></body></html>`

  const blob = new Blob([html], { type: 'text/html' })
  const url = URL.createObjectURL(blob); const a = document.createElement('a')
  a.href = url; a.download = filename; a.click(); URL.revokeObjectURL(url)
}




export function LanguageAnalysisPage() {
  const langStore = useLanguageStore()
  const {
    tab, setTab, text, setText, model, setModel, domain, setDomain,
    starRating, setStarRating,
    includeLime, setIncludeLime, includeAbsa, setIncludeAbsa,
    includeSarcasm, setIncludeSarcasm,
    data, setData, feedbackSent, setFeedbackSent,
    selectedCorrection, setSelectedCorrection,
    resetSingle: _resetSingle,
    // Batch tab
    bFileName, setBFileName, bTextCol, setBTextCol,
    bModel, setBModel, bRunAbsa, setBRunAbsa,
    bRunSarcasm, setBRunSarcasm, bIsMultilingual, setBIsMultilingual: _setBIsMultilingual,
    bShowAll, setBShowAll,
    bStartedAt, setBStartedAt, bStage, setBStage,
    bJobId: storedBJobId, setBJobId: setStoredBJobId,
    bResult: storedBResult, setBResult: setStoredBResult,
    setBColumns: setStoredBColumns,
    setBPreview: setStoredBPreview,
    resetBatch,
  } = langStore

  // File object is local (can't persist in ref)
  const [bFile, setBFile] = useState<File | null>(null)

  const { data: langData, loading, error, run, reset: _langReset } = useLanguage()
  const { showToast, state: appState } = useApp()
  const { confidenceThreshold } = appState
  const bulk = useBulk()
  const trendPoints = useTrendStore()

  // Timer: elapsed is derived from startedAt without re-rendering every second.
  const bNowRef = useRef(Date.now())
  useEffect(() => {
    if (bStage !== 'processing') return
    const h = setInterval(() => { bNowRef.current = Date.now() }, 1000)
    return () => clearInterval(h)
  }, [bStage])
  const bElapsed = bStartedAt ? Math.floor((bNowRef.current - bStartedAt) / 1000) : 0

  // Sync useLanguage result into the store (single tab)
  useEffect(() => {
    if (langData) setData(langData)
  }, [langData, setData])

  // Effective batch result: prefer live bulk data, fall back to stored
  const bResult = bulk.result || storedBResult

  // Sync useBulk results into the store (batch tab)
  useEffect(() => {
    if (bulk.result) setStoredBResult(bulk.result)
  }, [bulk.result, setStoredBResult])
  useEffect(() => {
    if (bulk.columns.length > 0) setStoredBColumns(bulk.columns)
  }, [bulk.columns, setStoredBColumns])
  useEffect(() => {
    if (bulk.preview.length > 0) setStoredBPreview(bulk.preview)
  }, [bulk.preview, setStoredBPreview])
  useEffect(() => {
    if (bulk.result?.job_id && bulk.result.job_id !== storedBJobId) {
      setStoredBJobId(bulk.result.job_id)
    }
  }, [bulk.result?.job_id, storedBJobId, setStoredBJobId])

  // Resume polling on remount if batch job was in-progress
  const hasResumed = useRef(false)
  useEffect(() => {
    if (hasResumed.current) return
    if (bStage === 'processing' && storedBJobId) {
      hasResumed.current = true
      bulk.resumePolling(storedBJobId)
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (bStage === 'processing') {
      if (!hasResumed.current || !bStartedAt) {
        // logs are reset in handleBSubmit
      }
      // bStartedAt is set in handleBSubmit — no timer to manage here
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [bStage])

  useEffect(() => {
    if (bResult?.status === 'completed' && bStage === 'processing') {
      if (bResult.results && bResult.results.length > 0) {
        pushTrendPoint(bResult.results)
      }
      setBStage('results')
    }
  }, [bResult?.status, bResult?.results, bStage, setBStage])

  const handleBFileSelect = useCallback(async (f: File) => {
    setBFile(f)
    setBFileName(f.name)
    const cols = await bulk.previewColumns(f)
    if (cols.length > 0) { setBTextCol(cols[0]); setBStage('configure') }
  }, [bulk, setBFileName, setBTextCol, setBStage])

  const handleBSubmit = useCallback(async () => {
    if (!bFile) return
    hasResumed.current = false
    setBStage('processing')
    setBStartedAt(Date.now())
    setStoredBJobId(null)
    // Pass bIsMultilingual — this page supports both modes
    await bulk.submit(bFile, bTextCol, bModel, bRunAbsa, bRunSarcasm, bIsMultilingual)
  }, [bFile, bTextCol, bModel, bRunAbsa, bRunSarcasm, bIsMultilingual, bulk, setBStage, setBStartedAt, setStoredBJobId])

  const handleBReset = useCallback(() => {
    bulk.reset()
    resetBatch()
    setBFile(null)
    hasResumed.current = false
  }, [bulk, resetBatch])

  const bTopKeywords = useMemo(() => {
    // FIX-3: Only compute heavy O(n) loop after analysis completes
    if (!bResult?.results || bResult.status !== 'completed') return []
    const wordCounts: Record<string, { positive: number; negative: number }> = {}
    bResult.results.forEach(r => {
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
  }, [bResult?.results, bResult?.status])

  // Compute batch-based trend data from bulk results (mirrors BulkAnalysisPage logic)
  const bTrendData = useMemo(() => {
    // FIX-3: Only compute after completion — was running O(n) every 500ms
    if (!bResult?.results || bResult.status !== 'completed' || bResult.results.length < 5) return undefined
    const batchSize = Math.max(1, Math.floor(bResult.results.length / 6))
    const batches = []
    for (let i = 0; i < bResult.results.length; i += batchSize) {
      const batch = bResult.results.slice(i, i + batchSize)
      const total = batch.length || 1
      batches.push({
        month: `Batch ${batches.length + 1}`,
        positive: Math.round(batch.filter(r => r.sentiment === 'positive').length / total * 100),
        negative: Math.round(batch.filter(r => r.sentiment === 'negative').length / total * 100),
        neutral: Math.round(batch.filter(r => r.sentiment === 'neutral').length / total * 100),
      })
    }
    return batches.slice(0, 6)
  }, [bResult?.results, bResult?.status])

  // Build language distribution data for bar chart using real server-detected language
  const bLangDistData = useMemo(() => {
    // FIX-3: Only compute after completion (language dist doesn't change during processing)
    if (!bResult?.results || bResult.status !== 'completed') return []
    const counts: Record<string, number> = {}
    bResult.results.forEach(r => {
      // Use backend-detected language; fall back to 'Unknown' only if missing
      const lang = r.detected_language ?? 'Unknown'
      counts[lang] = (counts[lang] || 0) + 1
    })
    const total = bResult.results.length
    return Object.entries(counts)
      .map(([language, count]) => ({
        language,
        count,
        percentage: Math.round((count / total) * 100),
      }))
      .sort((a, b) => b.count - a.count)
  }, [bResult?.results, bResult?.status])

  // Derive language count from the distribution data (same source of truth)
  const bLanguageCount = bLangDistData.length

  // Aggregate ABSA aspects from all batch rows (mirrors BulkAnalysisPage)
  const bTopAbsaAspects = useMemo(() => {
    // FIX-3: Only compute after completion — was running O(n) every 500ms
    if (!bResult?.results || bResult.status !== 'completed') return []
    const aspectMap: Record<string, { count: number; positive: number; negative: number; neutral: number; totalPolarity: number }> = {}
    bResult.results.forEach(row => {
      if (!row.aspects) return
      row.aspects.forEach(item => {
        const key = item.aspect.toLowerCase()
        if (!aspectMap[key]) aspectMap[key] = { count: 0, positive: 0, negative: 0, neutral: 0, totalPolarity: 0 }
        aspectMap[key].count++
        aspectMap[key].totalPolarity += item.polarity
        if (item.sentiment === 'positive') aspectMap[key].positive++
        else if (item.sentiment === 'negative') aspectMap[key].negative++
        else aspectMap[key].neutral++
      })
    })
    return Object.entries(aspectMap)
      .map(([aspect, d]) => ({
        aspect,
        count: d.count,
        positive: d.positive,
        negative: d.negative,
        neutral: d.neutral,
        avgPolarity: d.count > 0 ? d.totalPolarity / d.count : 0,
        // BUG-5 FIX: Use average polarity thresholds, NOT count mode
        dominantSentiment: (d.count > 0 ? d.totalPolarity / d.count : 0) > 0.20
          ? 'positive'
          : (d.count > 0 ? d.totalPolarity / d.count : 0) < -0.20
          ? 'negative'
          : 'neutral',
      }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 10)
  }, [bResult?.results, bResult?.status])

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

      {/* Tab System — Cyber Sliding Toggle */}
      <div className="tabs" data-active={tab} style={{ marginTop: 'var(--space-4)' }}>
        <button className={`tab-btn ${tab === 'single' ? 'tab-btn--active' : ''}`}
                onClick={() => setTab('single')}>
          <Icon3DTabSingle size={20} />
          <span>Multilingual Single Analysis</span>
          <div className="tab-glow" />
        </button>
        <button className={`tab-btn ${tab === 'batch' ? 'tab-btn--active' : ''}`}
                onClick={() => setTab('batch')}>
          <Icon3DTabBulk size={20} />
          <span>Multilingual Bulk Analysis</span>
          <div className="tab-glow" />
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
              <div className="form-group">
                <NeuralInputWrap>
                  <textarea id="lang-text" className="form-textarea"
                    style={{ minHeight: '160px' }}
                    placeholder="Enter a review in any language..."
                    value={text} onChange={e => setText(e.target.value)} maxLength={5000} />
                </NeuralInputWrap>

                {/* Auto-detect badge — below textarea, centered, 3D pill */}
                <div style={{ display: 'flex', justifyContent: 'center', marginTop: '10px' }}>
                  <div style={{
                    display: 'inline-flex', alignItems: 'center', gap: '10px',
                    padding: '6px 16px',
                    background: 'linear-gradient(135deg, rgba(0,217,255,0.07), rgba(0,255,136,0.05))',
                    border: '1px solid rgba(0,217,255,0.22)',
                    borderRadius: '9999px',
                    boxShadow: '0 0 14px rgba(0,217,255,0.12), inset 0 1px 0 rgba(255,255,255,0.06)',
                    backdropFilter: 'blur(8px)',
                    animation: 'detect-badge-shimmer 3s ease-in-out infinite',
                  }}>
                    {/* 3D Globe icon */}
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" style={{ flexShrink: 0 }}>
                      <defs>
                        <linearGradient id="det-glob" x1="0" y1="0" x2="24" y2="24">
                          <stop offset="0%" stopColor="#00FF88" />
                          <stop offset="100%" stopColor="#00D9FF" />
                        </linearGradient>
                      </defs>
                      <circle cx="12" cy="12" r="9" stroke="url(#det-glob)" strokeWidth="1.5" fill="url(#det-glob)" fillOpacity="0.1" />
                      <ellipse cx="12" cy="12" rx="5" ry="9" stroke="url(#det-glob)" strokeWidth="1" fill="none" opacity="0.5" />
                      <path d="M3 12h18M5 7h14M5 17h14" stroke="url(#det-glob)" strokeWidth="1" opacity="0.35" />
                      <circle cx="12" cy="12" r="2" fill="url(#det-glob)" opacity="0.8" />
                    </svg>
                    <span style={{ fontSize: 'var(--text-xs)', color: 'var(--color-positive)', fontWeight: 600, letterSpacing: '0.02em' }}>
                      Auto-detect enabled
                    </span>
                    {/* Vertical separator */}
                    <span style={{
                      width: '1px', height: '12px',
                      background: 'rgba(0,217,255,0.25)',
                      flexShrink: 0,
                      alignSelf: 'center',
                      display: 'block',
                    }} />
                    {/* Character counter — aligned to centre of separator */}
                    <span className="char-count" style={{
                      fontSize: 'var(--text-xs)',
                      fontFamily: 'var(--font-mono)',
                      lineHeight: 1,
                      display: 'inline-flex',
                      alignItems: 'center',
                      color: text.length > 4750 ? 'var(--color-negative)'
                        : text.length > 4000 ? 'var(--color-warning)'
                        : 'var(--color-text-muted)',
                    }}>
                      {text.length.toLocaleString()} / 5,000
                    </span>

                  </div>
                </div>
              </div>

              {/* Model / Domain / Star Rating — same as LivePredictionPage */}
              <div className="form-row" style={{ marginTop: 'var(--space-4)' }}>
                <div className="form-group" style={{ textAlign: 'center' }}>
                  <label className="form-label" htmlFor="lang-model-select" style={{ display: 'block', textAlign: 'center' }}>Model</label>
                  <NeuralSelect id="lang-model-select" value={model}
                    onChange={e => setModel(e.target.value as ModelChoice)}
                    options={MODELS.map(m => ({ label: capitalize(m), value: m }))} />
                </div>
                <div className="form-group" style={{ textAlign: 'center' }}>
                  <label className="form-label" htmlFor="lang-domain-select" style={{ display: 'block', textAlign: 'center' }}>Domain</label>
                  <NeuralSelect id="lang-domain-select" value={domain}
                    onChange={e => setDomain(e.target.value as DomainChoice)}
                    options={DOMAINS.map(d => ({ label: capitalize(d), value: d }))} />
                </div>
                <div className="form-group" style={{ textAlign: 'center' }}>
                  <label className="form-label" htmlFor="lang-star-select" style={{ display: 'block', textAlign: 'center' }}>Star Rating</label>
                  <NeuralSelect id="lang-star-select" value={starRating ?? ''}
                    onChange={e => setStarRating(e.target.value ? Number(e.target.value) : null)}
                    options={[
                      { label: 'None', value: '' },
                      ...[1,2,3,4,5].map(n => ({ label: '★'.repeat(n), value: n }))
                    ]} />
                </div>
              </div>

              {/* Toggles — LIME / ABSA / Sarcasm, same as LivePredictionPage */}
              <div className="toggle-row" style={{ marginTop: 'var(--space-4)', display: 'flex', justifyContent: 'space-between', flexWrap: 'wrap', alignItems: 'center', padding: '0 var(--space-2)' }}>
                <div style={{ flex: 1, display: 'flex', justifyContent: 'center' }}>
                  <HoloToggle label="LIME Explanation" checked={includeLime} onChange={setIncludeLime} />
                </div>
                <div style={{ flex: 1, display: 'flex', justifyContent: 'center' }}>
                  <HoloToggle label="ABSA" checked={includeAbsa} onChange={setIncludeAbsa} />
                </div>
                <div style={{ flex: 1, display: 'flex', justifyContent: 'center' }}>
                  <HoloToggle label="Sarcasm Detection" checked={includeSarcasm} onChange={setIncludeSarcasm} />
                </div>
              </div>

              <div style={{ display: 'flex', justifyContent: 'center', marginTop: 'var(--space-5)' }}>
                <NeuralButton size="lg" style={{ justifyContent: 'center', width: 'calc(100% - 8px)' }}
                    onClick={() => {
                      setFeedbackSent(false)
                      setSelectedCorrection(null)
                      run({
                        text, model,
                        domain,
                        star_rating: starRating,
                        include_lime: includeLime,
                        include_absa: includeAbsa,
                        include_sarcasm: includeSarcasm,
                      })
                    }} disabled={!text.trim() || loading}>
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
                    {/* Low-confidence warning (global threshold from Sidebar) */}
                    {data.confidence < confidenceThreshold * 100 && (
                      <div style={{
                        width: '100%', marginTop: 'var(--space-2)',
                        padding: '7px 14px',
                        background: 'rgba(245,158,11,0.08)',
                        border: '1px solid rgba(245,158,11,0.25)',
                        borderRadius: '8px',
                        display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px',
                        fontSize: 'var(--text-xs)', color: 'var(--color-neutral-sent)',
                        textAlign: 'center',
                      }}>
                        <span style={{ fontWeight: 700 }}>⚠ Low Confidence</span>
                        <span>Result ({data.confidence.toFixed(1)}%) is below your threshold ({(confidenceThreshold * 100).toFixed(0)}%). Interpret with caution.</span>
                      </div>
                    )}
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
                  <div className="ai-summary__item" style={{ justifyContent: 'flex-start', textAlign: 'left' }}>
                    <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}><Icon3DSentiment size={16} /></span>
                    <span><strong>Sentiment:</strong> The review expresses a <strong>{data.sentiment}</strong> opinion with <strong>{data.confidence.toFixed(1)}%</strong> model confidence.</span>
                  </div>
                  <div className="ai-summary__item" style={{ justifyContent: 'flex-start', textAlign: 'left' }}>
                    <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}><Icon3DChart size={16} /></span>
                    <span><strong>Polarity:</strong> Score of <strong>{data.polarity.toFixed(3)}</strong> indicates a {data.polarity > 0.3 ? 'positive' : data.polarity < -0.3 ? 'negative' : 'balanced'} tone.</span>
                  </div>
                  <div className="ai-summary__item" style={{ justifyContent: 'flex-start', textAlign: 'left' }}>
                    <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}><Icon3DTotal size={16} /></span>
                    <span><strong>Subjectivity:</strong> At <strong>{subjectivity.toFixed(3)}</strong>, the text is {subjectivity > 0.6 ? 'highly' : 'moderately'} subjective.</span>
                  </div>
                  <div className="ai-summary__item" style={{ justifyContent: 'flex-start', textAlign: 'left' }}>
                    <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}><Icon3DGlobe size={16} /></span>
                    <span><strong>Reliability:</strong> {data.confidence > 80 ? 'High confidence level, results are reliable.' : 'Confidence level is low, suggesting uncertain interpretation.'}</span>
                  </div>
                </div>
              </div>

              {/* ── LIME Explanation (real, gated on toggle + data) ── */}
              {includeLime && data.lime_features && data.lime_features.length > 0 && (
                <div className="card animate-in animate-in--d5 card--animated" style={{ marginTop: 'var(--space-4)' }}>
                  <SectionHeader icon={<Icon3DLIME size={22} />} title="LIME Explanation" subtitle="Local Interpretable Model Explanations · Cached for speed" />
                  <div className="card-body">
                    {/* Inline word highlighting */}
                    <div className="lime-sentence" style={{ textAlign: 'center' }}>
                      {(data.translated_text || text).split(/\s+/).map((word, i) => {
                        const feature = data.lime_features?.find(
                          f => f.word.toLowerCase() === word.toLowerCase().replace(/[^a-z]/g, ''))
                        const cls = feature
                          ? feature.weight > 0 ? 'lime-word--positive' : 'lime-word--negative'
                          : ''
                        return (
                          <span key={i} className={`lime-word ${cls}`}
                                title={feature ? `Weight: ${feature.weight.toFixed(4)}` : ''}>
                            {word}{' '}
                          </span>
                        )
                      })}
                    </div>
                    {/* Feature contributions bar chart */}
                    <h4 className="result-section__title" style={{ marginTop: 'var(--space-4)', textAlign: 'center' }}>
                      Top Feature Contributions
                    </h4>
                    <LIMEChart features={data.lime_features} />
                  </div>
                </div>
              )}

              {/* ── ABSA (real, gated on toggle + data) ── */}
              {includeAbsa && data.absa && data.absa.length > 0 ? (
                <div className="card animate-in card--animated" style={{ marginTop: 'var(--space-4)' }}>
                  <SectionHeader icon={<Icon3DResults size={22} />} title="Aspect-Based Sentiment Analysis" subtitle="Fine-grained aspect-level sentiment" />
                  <div className="card-body">
                    <table className="absa-table">
                      <thead><tr>
                        <th>Aspect</th><th>Sentiment</th><th>Confidence</th><th>Score</th>
                      </tr></thead>
                      <tbody>
                        {data.absa.map((item, i) => (
                          <tr key={i} style={{ animationDelay: `${i * 0.05}s` }} className="animate-in">
                            <td className="absa-aspect-term">{item.aspect}</td>
                            <td><span className={`badge badge--${item.sentiment}`}>
                              {item.sentiment}
                            </span></td>
                            <td>
                              <div className="absa-conf-bar">
                                <div className="prog-bar">
                                  <div className={`prog-bar__fill prog-bar__fill--${item.sentiment === 'positive' ? 'positive' : item.sentiment === 'negative' ? 'negative' : 'neutral'}`}
                                       style={{ width: `${Math.abs(item.polarity) * 100}%` }} />
                                </div>
                              </div>
                            </td>
                            <td style={{ fontFamily: 'var(--font-mono)' }}>
                              {item.polarity.toFixed(3)}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              ) : (
                includeAbsa && !loading && data && (
                  <div className="card card--animated" style={{ marginTop: 'var(--space-4)', textAlign: 'center' }}>
                    <SectionHeader icon={<Icon3DResults size={22} />} title="Aspect-Based Sentiment Analysis" subtitle="Fine-grained aspect-level sentiment" />
                    <p className="helper-text" style={{ padding: 'var(--space-5)', textAlign: 'center' }}>No aspects detected — try a more detailed review</p>
                  </div>
                )
              )}

              {/* ── Sarcasm Detection (real, gated on toggle + data) ── */}
              {includeSarcasm && data.sarcasm && (
                <div className={`card animate-in card--animated ${data.sarcasm.detected ? 'sarcasm-card--detected' : 'sarcasm-card--clean'}`}
                     style={{ marginTop: 'var(--space-4)', padding: 'var(--space-5)' }}>
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '10px', textAlign: 'center' }}>
                    <div style={{
                      display: 'inline-flex', alignItems: 'center', gap: '10px',
                      background: data.sarcasm.detected ? 'rgba(244, 63, 94, 0.08)' : 'rgba(0, 217, 255, 0.06)',
                      border: `1px solid ${data.sarcasm.detected ? 'rgba(244, 63, 94, 0.2)' : 'rgba(0, 217, 255, 0.15)'}`,
                      borderRadius: '12px', padding: '8px 20px',
                    }}>
                      <span style={{ display: 'inline-flex', alignItems: 'center' }}>
                        {data.sarcasm.detected
                          ? <svg width="22" height="22" viewBox="0 0 48 48" style={icon3dStyle} fill="none"><defs><linearGradient id="lshield3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#A78BFA"/><stop offset="100%" stopColor="#F43F5E"/></linearGradient></defs><path d="M24 4L6 14v12c0 12 8 16 18 18 10-2 18-6 18-18V14L24 4z" stroke="url(#lshield3d)" strokeWidth="2" fill="url(#lshield3d)" fillOpacity=".1" /><path d="M18 24l4 4 8-8" stroke="url(#lshield3d)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" /></svg>
                          : <svg width="22" height="22" viewBox="0 0 48 48" style={icon3dStyle} fill="none"><defs><linearGradient id="lchk3d" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#22C55E"/><stop offset="100%" stopColor="#00FF88"/></linearGradient></defs><circle cx="24" cy="24" r="18" stroke="url(#lchk3d)" strokeWidth="2" fill="url(#lchk3d)" fillOpacity=".1" /><path d="M16 24l5 5 11-11" stroke="url(#lchk3d)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" /></svg>
                        }
                      </span>
                      <span style={{ fontSize: 'var(--text-base)', fontWeight: 700, color: 'var(--color-text)' }}>
                        {data.sarcasm.detected ? 'Sarcasm Detected' : 'No Sarcasm Detected'}
                      </span>
                    </div>
                    <div style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)' }}>
                      {data.sarcasm.detected
                        ? 'This review may contain ironic or sarcastic language.'
                        : 'The model found no indicators of sarcasm.'}
                    </div>
                  </div>
                </div>
              )}

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
                    generatePDF(data as unknown as Record<string, unknown>, keywords, 'language-result.html')
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
                      display: 'inline-flex', flexDirection: 'column', alignItems: 'center', gap: '8px',
                      padding: '16px 32px',
                      background: 'rgba(34,197,94,0.08)', border: '1px solid rgba(34,197,94,0.2)',
                      borderRadius: '12px', margin: '8px 0'
                    }}>
                  <div style={{ marginBottom: '2px' }}>
                    <svg width="28" height="28" viewBox="0 0 48 48" style={{ filter: 'drop-shadow(0 0 8px rgba(34,197,94,0.3))' }} fill="none">
                      <defs><linearGradient id="feedback-ok2" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#22C55E"/><stop offset="100%" stopColor="#2DD4BF"/></linearGradient></defs>
                      <circle cx="24" cy="24" r="18" stroke="url(#feedback-ok2)" strokeWidth="2" fill="url(#feedback-ok2)" fillOpacity=".1"/>
                      <path d="M14 24l8 8 12-14" stroke="url(#feedback-ok2)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  </div>
                      <span style={{ fontSize: 'var(--text-base)', color: 'var(--color-positive)', fontWeight: 700 }}>Thank you for your feedback!</span>
                      <span style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)' }}>
                        Corrected to: <strong>{selectedCorrection ? selectedCorrection.charAt(0).toUpperCase() + selectedCorrection.slice(1) : ''}</strong>
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
                                await fetch(`${import.meta.env.VITE_API_URL}/feedback/submit`, {
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
                <NeuralButton variant="ghost" onClick={() => { _resetSingle(); setText(''); }}>
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

          {bStage === 'configure' && (bFile ? (
            <>
              {/* ── Card 1: File Uploaded ── */}
              <div className="card animate-in card--animated">
                <SectionHeader icon={<Icon3DFile size={22} />} title="File Uploaded" subtitle="Review your uploaded dataset" />
                <div className="card-body" style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', flexDirection: 'column', gap: '8px', textAlign: 'center' }}>
                  <div>
                    <div style={{ fontWeight: 600 }}>{bFile.name}</div>
                    <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)', marginTop: 2 }}>
                      {(bFile.size / 1024).toFixed(0)} KB · {bulk.columns.length} columns detected · Ready
                    </div>
                  </div>
                  <NeuralButton variant="ghost" size="sm"
                          onClick={() => { setBFile(null); setBStage('upload'); bulk.reset() }}>
                    Change File
                  </NeuralButton>
                </div>
              </div>

              {/* ── Card 2: Column Mapping ── */}
              <div className="card animate-in animate-in--d1 card--animated" style={{ marginTop: 'var(--space-4)' }}>
                <SectionHeader icon={<Icon3DColumns size={22} />} title="Column Mapping" subtitle="Select the text column for analysis" />
                <div className="card-body">
                  <div className="form-group" style={{ textAlign: 'center' }}>
                    <label className="form-label" htmlFor="lang-text-col" style={{ textAlign: 'center', display: 'block' }}>Text Column</label>
                    <NeuralInputWrap>
                      <select id="lang-text-col" className="form-select" value={bTextCol}
                              onChange={e => setBTextCol(e.target.value)}>
                        {bulk.columns.map(c => <option key={c} value={c}>{c}</option>)}
                      </select>
                    </NeuralInputWrap>
                  </div>
                  {bulk.preview.length > 0 && (
                    <div className="preview-table-wrap" style={{ marginTop: 'var(--space-4)' }}>
                      <table className="preview-table">
                        <thead><tr><th style={{ textAlign: 'center' }}>Row</th><th style={{ textAlign: 'center' }}>{bTextCol}</th></tr></thead>
                        <tbody>
                          {bulk.preview.slice(0, 5).map((row, i) => (
                            <tr key={i}><td style={{ textAlign: 'center' }}>{i + 1}</td><td style={{ textAlign: 'center' }}>{String(row[bTextCol] ?? '').slice(0, 100)}</td></tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              </div>

              {/* ── Card 3: Analysis Settings ── */}
              <div className="card animate-in animate-in--d2 card--animated" style={{ marginTop: 'var(--space-4)' }}>
                <SectionHeader icon={<Icon3DGearSettings size={22} />} title="Analysis Settings" subtitle="Configure model and detection options" />
                <div className="card-body">
                  <div className="form-group" style={{ textAlign: 'center' }}>
                    <label className="form-label" htmlFor="lang-bulk-model" style={{ textAlign: 'center', display: 'block' }}>Model</label>
                    <NeuralInputWrap>
                      <select id="lang-bulk-model" className="form-select" value={bModel}
                              onChange={e => setBModel(e.target.value)}>
                        {['best','LinearSVC','LogisticRegression','NaiveBayes','RandomForest'].map(m =>
                          <option key={m} value={m}>{m === 'best' ? 'Best' : m.replace(/([A-Z])/g, ' $1').trim()}</option>)}
                      </select>
                    </NeuralInputWrap>
                  </div>
                  {/* Only ABSA + Sarcasm — this page is always multilingual, no toggle needed */}
                  <div style={{ display: 'flex', justifyContent: 'center', gap: 'var(--space-8)', flexWrap: 'wrap', marginTop: 'var(--space-4)' }}>
                    <HoloToggle label="ABSA (Slower)" checked={bRunAbsa} onChange={setBRunAbsa} />
                    <HoloToggle label="Sarcasm Detection" checked={bRunSarcasm} onChange={setBRunSarcasm} />
                  </div>
                </div>
              </div>

              {/* ── Analyze button ── */}
              <div style={{ display: 'flex', justifyContent: 'center', marginTop: 'var(--space-4)' }}>
                <NeuralButton size="lg" style={{ width: 'calc(100% - 8px)', justifyContent: 'center' }}
                        onClick={handleBSubmit}>
                  Translate &amp; Analyze All
                </NeuralButton>
              </div>
            </>
          ) : (
            /* Scenario B: configure stage but file lost after navigation */
            <div className="card animate-in card--animated">
              <SectionHeader icon={<Icon3DFile size={22} />} title="File Selection Lost" subtitle="Your previous file selection was lost. Please re-upload your file." />
              <div className="card-body" style={{ textAlign: 'center' }}>
                {bFileName && <div style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)', marginBottom: 'var(--space-3)' }}>Previous file: {bFileName}</div>}
                <FolderUpload onFileSelect={handleBFileSelect} />
              </div>
            </div>
          ))}

          {bStage === 'processing' && (() => {
            // ── Live stats from streaming results (bResult updates every 250ms poll) ──
            const rows = bResult?.results ?? []
            const processed = bResult?.processed ?? 0
            const total = bResult?.total_rows ?? 0
            // Use server-provided exact progress percentage which accounts for all 3 phases
            const progressPct = bResult?.progress ? Math.round(bResult.progress) : (total > 0 ? Math.round((processed / total) * 100) : 0)
            const speed = bElapsed > 0 ? (processed / bElapsed).toFixed(1) : '0.0'
            const avgConf = rows.length > 0 ? (rows.reduce((s, r) => s + r.confidence, 0) / rows.length).toFixed(1) : '—'
            const errorCount = rows.filter(r => r.sentiment === 'error' || r.sentiment === 'unknown').length

            // ── Live sentiment distribution — use server-provided cumulative counts
            // (NOT from rows[] which is capped at 50 for network efficiency)
            const posCount     = bResult?.live_pos     ?? rows.filter(r => r.sentiment === 'positive').length
            const negCount     = bResult?.live_neg     ?? rows.filter(r => r.sentiment === 'negative').length
            const neuCount     = bResult?.live_neu     ?? rows.filter(r => r.sentiment === 'neutral').length
            const sentRealTotal = posCount + negCount + neuCount
            const hasSentimentData = sentRealTotal > 0
            const sentTotal = sentRealTotal || 1
            const posPct = Math.round((posCount / sentTotal) * 100)
            const negPct = Math.round((negCount / sentTotal) * 100)
            const neuPct = 100 - posPct - negPct

            // ── Live language counts (top 4) ──
            const langMap: Record<string, number> = {}
            rows.forEach(r => { const l = r.detected_language ?? 'Unknown'; langMap[l] = (langMap[l] || 0) + 1 })
            const topLangs = Object.entries(langMap).sort((a, b) => b[1] - a[1]).slice(0, 4)
            const langMax = topLangs[0]?.[1] ?? 1

            // ── Shared styles ──
            const statLabel: React.CSSProperties = {
              fontSize: '10px', color: 'var(--color-text-faint)',
              textTransform: 'uppercase', letterSpacing: '0.06em',
            }
            const statValue: React.CSSProperties = {
              fontSize: '13px', fontWeight: 700, fontFamily: 'var(--font-mono)',
              color: 'var(--color-text)', transition: 'all 0.3s ease',
            }

            return (
            <div className="card animate-in" style={{ padding: '16px' }}>
              <div style={{
                display: 'grid',
                gridTemplateColumns: '190px 1fr 190px',
                gridTemplateRows: '1fr 1fr',
                gap: '12px',
              }}>

                {/* ── TOP-LEFT: Live Stats ── */}
                <CyberCard style={{ gridColumn: 1, gridRow: 1 }}>
                  <PanelBadge icon={<Icon3DPulse />} label="Live Stats"
                    bg="rgba(0,217,255,0.06)" border="rgba(0,217,255,0.18)" color="#00d9ff" />
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '7px', flex: 1, justifyContent: 'center' }}>
                    {[
                      { label: 'Processed', value: `${processed} / ${total || '?'}`, color: 'var(--color-primary-bright)' },
                      { label: 'Speed', value: `${speed} r/s`, color: '#2dd4bf' },
                      { label: 'Avg Conf', value: avgConf === '—' ? '—' : `${avgConf}%`, color: '#a78bfa' },
                      { label: 'Errors', value: String(errorCount), color: errorCount > 0 ? 'var(--color-negative)' : 'var(--color-positive)' },
                      { label: 'Progress', value: `${progressPct}%`, color: '#fde047' },
                    ].map(s => (
                      <div key={s.label} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={statLabel}>{s.label}</span>
                        <span style={{ ...statValue, color: s.color }}>{s.value}</span>
                      </div>
                    ))}
                  </div>
                </CyberCard>

                {/* ── TOP-RIGHT: Sentiment ── */}
                <CyberCard style={{ gridColumn: 3, gridRow: 1 }}>
                  <PanelBadge icon={<Icon3DSentimentPie />} label="Sentiment"
                    bg="rgba(34,197,94,0.06)" border="rgba(34,197,94,0.18)" color="#22c55e" />
                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px', flex: 1, justifyContent: 'center' }}>
                    {hasSentimentData ? (
                      <>
                        {/* CSS donut */}
                        <div style={{
                          width: '68px', height: '68px', borderRadius: '50%',
                          background: `conic-gradient(
                            #22c55e 0% ${posPct}%,
                            #f59e0b ${posPct}% ${posPct + neuPct}%,
                            #f43f5e ${posPct + neuPct}% 100%
                          )`,
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          transition: 'all 0.3s ease',
                        }}>
                          <div style={{
                            width: '44px', height: '44px', borderRadius: '50%',
                            background: 'var(--color-bg-card, #0f1923)',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                            fontSize: '11px', fontWeight: 700, color: 'var(--color-text)',
                            fontFamily: 'var(--font-mono)',
                          }}>
                            {sentRealTotal}
                          </div>
                        </div>
                        {/* Legend */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '4px', width: '100%' }}>
                          {[
                            { label: 'Positive', pct: posPct, color: '#22c55e' },
                            { label: 'Neutral', pct: neuPct, color: '#f59e0b' },
                            { label: 'Negative', pct: negPct, color: '#f43f5e' },
                          ].map(s => (
                            <div key={s.label}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', marginBottom: '2px' }}>
                                <span style={{ color: s.color, fontWeight: 600 }}>{s.label}</span>
                                <span style={{ color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>{s.pct}%</span>
                              </div>
                              <div style={{ height: '3px', borderRadius: '2px', background: 'rgba(255,255,255,0.06)' }}>
                                <div style={{
                                  height: '100%', borderRadius: '2px', background: s.color,
                                  width: `${s.pct}%`, transition: 'width 0.4s ease', opacity: 0.8,
                                }} />
                              </div>
                            </div>
                          ))}
                        </div>
                      </>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '10px', padding: '12px 0', flex: 1 }}>
                        <div style={{
                          width: '48px', height: '48px', borderRadius: '50%',
                          border: '2px dashed rgba(34,197,94,0.3)',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          animation: 'pulse 2s ease-in-out infinite',
                        }}>
                          <div style={{
                            fontSize: '11px', fontWeight: 700, color: 'var(--color-text-faint)',
                            fontFamily: 'var(--font-mono)',
                          }}>0</div>
                        </div>
                        <div style={{ fontSize: '10px', color: 'var(--color-text-faint)', textAlign: 'center', lineHeight: 1.4, letterSpacing: '0.02em' }}>
                          Awaiting data…
                        </div>
                      </div>
                    )}
                  </div>
                </CyberCard>

                {/* ── BOTTOM-LEFT: Config ── */}
                <CyberCard style={{ gridColumn: 1, gridRow: 2, opacity: 0.85 }}>
                  <PanelBadge icon={<Icon3DGearPanel />} label="Config"
                    bg="rgba(167,139,250,0.06)" border="rgba(167,139,250,0.18)" color="#a78bfa" />
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', fontSize: '11px', flex: 1, justifyContent: 'center' }}>
                    {[
                      ['Model', bModel === 'best' ? 'Best' : bModel],
                      ['ABSA', bRunAbsa ? 'ON' : 'OFF'],
                      ['Sarcasm', bRunSarcasm ? 'ON' : 'OFF'],
                    ].map(([k, v]) => (
                      <div key={k} style={{ display: 'flex', justifyContent: 'space-between' }}>
                        <span style={{ color: 'var(--color-text-faint)' }}>{k}</span>
                        <span style={{
                          fontWeight: 600, fontFamily: 'var(--font-mono)',
                          color: v === 'ON' ? 'var(--color-positive)' : v === 'OFF' ? 'var(--color-text-faint)' : 'var(--color-primary-bright)',
                        }}>{v}</span>
                      </div>
                    ))}
                  </div>
                </CyberCard>

                {/* ── BOTTOM-RIGHT: Languages ── */}
                <CyberCard style={{ gridColumn: 3, gridRow: 2, opacity: 0.85 }}>
                  <PanelBadge icon={<Icon3DGlobePanel />} label="Languages"
                    bg="rgba(244,63,94,0.06)" border="rgba(244,63,94,0.18)" color="#f43f5e" />
                  <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                    {topLangs.length > 0 ? (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                        {topLangs.map(([lang, cnt]) => (
                          <div key={lang}>
                            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '10px', marginBottom: '2px' }}>
                              <span style={{ color: 'var(--color-text)', fontWeight: 500 }}>{lang}</span>
                              <span style={{ color: 'var(--color-text-faint)', fontFamily: 'var(--font-mono)' }}>{cnt}</span>
                            </div>
                            <div style={{ height: '3px', borderRadius: '2px', background: 'rgba(255,255,255,0.06)' }}>
                              <div style={{
                                height: '100%', borderRadius: '2px',
                                background: 'linear-gradient(90deg, #a78bfa, #00d9ff)',
                                width: `${Math.round((cnt / langMax) * 100)}%`,
                                transition: 'width 0.4s ease', opacity: 0.7,
                              }} />
                            </div>
                          </div>
                        ))}
                      </div>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: '10px', padding: '12px 0', flex: 1 }}>
                        <div style={{
                          width: '48px', height: '48px', borderRadius: '50%',
                          border: '2px dashed rgba(244,63,94,0.3)',
                          display: 'flex', alignItems: 'center', justifyContent: 'center',
                          animation: 'pulse 2s ease-in-out infinite',
                        }}>
                          <div style={{
                            fontSize: '11px', fontWeight: 700, color: 'var(--color-text-faint)',
                            fontFamily: 'var(--font-mono)',
                          }}>0</div>
                        </div>
                        <div style={{ fontSize: '10px', color: 'var(--color-text-faint)', textAlign: 'center', lineHeight: 1.4, letterSpacing: '0.02em' }}>
                          Awaiting data…
                        </div>
                      </div>
                    )}
                  </div>
                </CyberCard>

                {/* ── CENTER: Loader + Progress Box + Status Pill + Terminal ── */}
                <div style={{
                  gridColumn: 2, gridRow: '1 / 3',
                  display: 'flex', flexDirection: 'column',
                  alignItems: 'center', justifyContent: 'center',
                  gap: 0,
                }}>
                  {/* CyberLoader — properly spaced away from card header */}
                  <div style={{ marginBottom: '-20px', display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
                    <CyberLoader scale={0.78} />
                  </div>

                  {/* ── Phase Progress 3D Sub-Box ── */}
                  {(() => {
                    const phase = bResult?.phase

                    const phaseIcons: Record<string, string> = {
                      init:        `<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><defs><linearGradient id="lpi0" x1="0" y1="0" x2="24" y2="24"><stop offset="0%" stop-color="#fde047"/><stop offset="100%" stop-color="#f59e0b"/></linearGradient></defs><circle cx="12" cy="12" r="10" stroke="url(#lpi0)" stroke-width="1.5" fill="url(#lpi0)" fill-opacity=".1"/><path d="M12 7v5l3 3" stroke="url(#lpi0)" stroke-width="1.5" stroke-linecap="round"/></svg>`,
                      detecting:   `<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><defs><linearGradient id="lpi1" x1="0" y1="0" x2="24" y2="24"><stop offset="0%" stop-color="#00d9ff"/><stop offset="100%" stop-color="#0ea5e9"/></linearGradient></defs><circle cx="10" cy="10" r="6" stroke="url(#lpi1)" stroke-width="1.5" fill="url(#lpi1)" fill-opacity=".1"/><path d="M14.5 14.5l4 4" stroke="url(#lpi1)" stroke-width="2" stroke-linecap="round"/></svg>`,
                      translating: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><defs><linearGradient id="lpi2" x1="0" y1="0" x2="24" y2="24"><stop offset="0%" stop-color="#a78bfa"/><stop offset="100%" stop-color="#7c3aed"/></linearGradient></defs><circle cx="12" cy="12" r="9" stroke="url(#lpi2)" stroke-width="1.5" fill="url(#lpi2)" fill-opacity=".1"/><ellipse cx="12" cy="12" rx="4" ry="9" stroke="url(#lpi2)" stroke-width="1" fill="none" opacity=".5"/><path d="M3 12h18" stroke="url(#lpi2)" stroke-width="1" opacity=".4"/></svg>`,
                      analyzing:   `<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><defs><linearGradient id="lpi3" x1="0" y1="0" x2="24" y2="24"><stop offset="0%" stop-color="#00ff88"/><stop offset="100%" stop-color="#22c55e"/></linearGradient></defs><path d="M13 2L4 14h7l-1 8 9-12h-7l1-8z" stroke="url(#lpi3)" stroke-width="1.5" stroke-linejoin="round" fill="url(#lpi3)" fill-opacity=".15"/></svg>`,
                      done:        `<svg width="16" height="16" viewBox="0 0 24 24" fill="none"><defs><linearGradient id="lpi4" x1="0" y1="0" x2="24" y2="24"><stop offset="0%" stop-color="#22c55e"/><stop offset="100%" stop-color="#00ff88"/></linearGradient></defs><circle cx="12" cy="12" r="9" stroke="url(#lpi4)" stroke-width="1.5" fill="url(#lpi4)" fill-opacity=".12"/><path d="M8 12l3 3 5-5" stroke="url(#lpi4)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
                    }

                    const PHASE_CONFIG: Record<string, { label: string; color: string; grad: string }> = {
                      init:        { label: 'Initializing',        color: '#fde047', grad: 'linear-gradient(90deg,#fde047,#f59e0b)' },
                      detecting:   { label: 'Detecting Languages', color: '#00d9ff', grad: 'linear-gradient(90deg,#00d9ff,#0ea5e9)' },
                      translating: { label: 'Translating',         color: '#a78bfa', grad: 'linear-gradient(90deg,#a78bfa,#7c3aed)' },
                      analyzing:   { label: 'Analyzing Sentiment', color: '#00ff88', grad: 'linear-gradient(90deg,#00ff88,#22c55e)' },
                      done:        { label: 'Finalizing',           color: '#22c55e', grad: 'linear-gradient(90deg,#22c55e,#16a34a)' },
                    }
                    const cfg = PHASE_CONFIG[phase ?? 'init'] ?? PHASE_CONFIG.init

                    const STEPS = [
                      { key: 'detecting',   label: 'Detect',    pct: 15  },
                      { key: 'translating', label: 'Translate', pct: 40  },
                      { key: 'analyzing',   label: 'Analyze',   pct: 68  },
                      { key: 'done',        label: 'Done',      pct: 100 },
                    ]

                    return (
                      <div style={{
                        width: '72%', maxWidth: '280px', alignSelf: 'center',
                        background: 'rgba(13,17,23,0.75)',
                        border: '1px solid rgba(0,217,255,0.20)',
                        borderRadius: '14px',
                        boxShadow: '0 0 18px rgba(0,217,255,0.08), inset 0 1px 0 rgba(255,255,255,0.04)',
                        backdropFilter: 'blur(10px)',
                        padding: '12px 16px 10px',
                        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '8px',
                        marginBottom: '10px',
                      }}>
                        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '7px', width: '100%' }}>
                          <span
                            dangerouslySetInnerHTML={{ __html: phaseIcons[phase ?? 'init'] ?? phaseIcons.init }}
                            style={{ display: 'flex', flexShrink: 0 }}
                          />
                          <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: cfg.color, fontWeight: 700, letterSpacing: '0.06em' }}>
                            {cfg.label}
                          </span>
                          <span style={{
                            fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--color-text-faint)',
                            background: 'rgba(255,255,255,0.05)', padding: '1px 6px', borderRadius: '6px',
                            border: '1px solid rgba(255,255,255,0.07)',
                          }}>{progressPct}%</span>
                        </div>
                        <div style={{ width: '100%', height: '4px', borderRadius: '3px', background: 'rgba(255,255,255,0.06)', overflow: 'hidden' }}>
                          <div style={{
                            height: '100%', borderRadius: '3px', background: cfg.grad,
                            width: `${progressPct}%`, transition: 'width 0.5s ease',
                            boxShadow: `0 0 6px ${cfg.color}55`,
                          }} />
                        </div>
                        <div style={{ display: 'flex', justifyContent: 'space-between', width: '100%', paddingTop: '2px' }}>
                          {STEPS.map(step => {
                            const stepDone   = progressPct >= step.pct
                            const stepActive = bResult?.phase === step.key
                            return (
                              <div key={step.key} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '3px' }}>
                                <div style={{
                                  width: '7px', height: '7px', borderRadius: '50%',
                                  background: stepDone ? '#00ff88' : 'rgba(255,255,255,0.12)',
                                  boxShadow: stepActive ? '0 0 8px #00ff88' : 'none',
                                  transition: 'all 0.3s ease',
                                }} />
                                <span style={{ fontSize: '7px', color: stepDone ? 'var(--color-text-muted)' : 'var(--color-text-faint)', fontFamily: 'var(--font-mono)' }}>{step.label}</span>
                              </div>
                            )
                          })}
                        </div>
                      </div>
                    )
                  })()}

                  {/* Spacer pushes status pill to visual centre */}
                  <div style={{ flex: 1 }} />

                  {/* Status pill — centred between progress box and terminal */}
                  <div style={{
                    display: 'inline-flex', alignItems: 'center', gap: '8px',
                    background: 'rgba(0, 217, 255, 0.06)', border: '1px solid rgba(0, 217, 255, 0.15)',
                    borderRadius: '12px', padding: '5px 14px', whiteSpace: 'nowrap',
                  }}>
                    <span style={{ fontSize: '11px', color: 'var(--color-primary-bright)', fontWeight: 600 }}>
                      Translating &amp; Analyzing
                    </span>
                    <span style={{ fontSize: '10px', color: 'var(--color-text-muted)', fontFamily: 'var(--font-mono)' }}>
                      {processed}/{total || '?'} · {Math.floor(bElapsed / 60)}m {bElapsed % 60}s
                    </span>
                  </div>

                  {/* Spacer pushes terminal down */}
                  <div style={{ flex: 1 }} />

                  {/* Terminal logs */}

                  <div style={{
                    width: '90%', maxWidth: '380px',
                    background: 'rgba(0, 0, 0, 0.4)', border: '1px solid rgba(0, 217, 255, 0.1)',
                    borderRadius: '10px', overflow: 'hidden',
                  }}>
                    <div style={{
                      display: 'flex', alignItems: 'center', gap: '5px',
                      padding: '5px 10px', borderBottom: '1px solid rgba(255,255,255,0.06)',
                      background: 'rgba(0,0,0,0.3)',
                    }}>
                      <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#ff5f57' }} />
                      <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#ffbd2e' }} />
                      <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#28ca41' }} />
                      <span style={{ flex: 1, textAlign: 'center', fontSize: '8px', color: 'var(--color-text-faint)', fontFamily: 'var(--font-mono)', letterSpacing: '0.05em' }}>
                        ANALYSIS TERMINAL
                      </span>
                    </div>
                    <div style={{
                      padding: '6px 10px', height: '90px', overflowY: 'auto',
                      display: 'flex', flexDirection: 'column', gap: '2px',
                      fontFamily: 'var(--font-mono)', fontSize: '9px', lineHeight: '1.5',
                    }}>
                      {(bResult?.logs ?? ['Starting multilingual analysis pipeline...']).map((line, i) => (
                        <div key={i} style={{ color: i === 0 ? 'var(--color-text-faint)' : 'var(--color-text)' }}>
                          <span style={{ color: '#28ca41', marginRight: '4px', fontWeight: 700 }}>❯</span>
                          {line}
                        </div>
                      ))}
                    </div>
                  </div>

                  <NeuralButton variant="ghost" size="sm" onClick={handleBReset}>Cancel</NeuralButton>
                </div>

              </div>
            </div>
            )
          })()}

          {bStage === 'results' && bResult?.summary && (
            <>
              {/* KPI Cards */}
              <div className="kpi-grid">
                <div className="card kpi-card kpi-card--total" style={{ textAlign: 'center' }}>
                  <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '6px' }}><Icon3DTotal size={20} /></div>
                  <div className="kpi-card__tag" style={{ textAlign: 'center' }}>Total</div>
                  <div className="kpi-card__value" style={{ textAlign: 'center' }}>{bResult.summary.total_analyzed}</div>
                  <div className="kpi-card__sub" style={{ textAlign: 'center' }}>reviews</div>
                </div>
                <div className="card kpi-card kpi-card--positive" style={{ textAlign: 'center' }}>
                  <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '6px' }}><Icon3DPositive size={20} /></div>
                  <div className="kpi-card__tag" style={{ textAlign: 'center' }}>Positive</div>
                  <div className="kpi-card__value" style={{ textAlign: 'center' }}>{bResult.summary.positive_pct}%</div>
                  <div className="kpi-card__sub" style={{ textAlign: 'center' }}>{bResult.summary.positive} reviews</div>
                </div>
                <div className="card kpi-card kpi-card--negative" style={{ textAlign: 'center' }}>
                  <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '6px' }}><Icon3DNegative size={20} /></div>
                  <div className="kpi-card__tag" style={{ textAlign: 'center' }}>Negative</div>
                  <div className="kpi-card__value" style={{ textAlign: 'center' }}>{bResult.summary.negative_pct}%</div>
                  <div className="kpi-card__sub" style={{ textAlign: 'center' }}>{bResult.summary.negative} reviews</div>
                </div>
                <div className="card kpi-card kpi-card--neutral" style={{ textAlign: 'center' }}>
                  <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '6px' }}><Icon3DNeutral size={20} /></div>
                  <div className="kpi-card__tag" style={{ textAlign: 'center' }}>Neutral</div>
                  <div className="kpi-card__value" style={{ textAlign: 'center' }}>{bResult.summary.neutral_pct}%</div>
                  <div className="kpi-card__sub" style={{ textAlign: 'center' }}>{bResult.summary.neutral} reviews</div>
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
                      <th style={{ width: '40px', textAlign: 'center' }}>#</th>
                      <th style={{ width: '22%', textAlign: 'center' }}>Review (Original)</th>
                      <th style={{ textAlign: 'center' }}>Language</th>
                      <th style={{ width: '22%', textAlign: 'center' }}>Translated to English</th>
                      <th style={{ textAlign: 'center' }}>Sentiment</th>
                      <th style={{ textAlign: 'center' }}>Confidence</th>
                      {bRunSarcasm && <th style={{ textAlign: 'center' }}>Sarcasm</th>}
                    </tr></thead>
                    <tbody>
                      {(bShowAll ? bResult.results ?? [] : (bResult.results ?? []).slice(0, 10)).map(row => {
                        // Use real server-detected language and translation — same as BulkAnalysisPage
                        const detectedLang = row.detected_language ?? '\u2014'
                        const belowThreshold = row.confidence < confidenceThreshold * 100
                        // Review column = original text; Translated = only row.translated_text (dash if none)
                        const originalText = row.text
                        const translatedEn = row.translated_text ?? null
                        return (
                          <tr key={row.row_index} style={belowThreshold ? { opacity: 0.5 } : undefined}>
                            <td style={{ fontFamily: 'var(--font-mono)', color: 'var(--color-text-faint)', textAlign: 'center' }}>{row.row_index}</td>
                            {/* ORIGINAL language text — always from row.text */}
                            <td style={{ textAlign: 'left', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={originalText}>
                              {originalText.slice(0, 50)}{originalText.length > 50 ? '\u2026' : ''}
                            </td>
                            <td style={{ textAlign: 'center' }}>
                              <span className="badge badge-info" style={{ fontSize: '10px' }}>{detectedLang}</span>
                            </td>
                            {/* TRANSLATED text — only row.translated_text, dash if not available */}
                            <td style={{ textAlign: 'center', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap', fontSize: 'var(--text-xs)', color: 'var(--color-text-muted)' }} title={translatedEn ?? ''}>
                              {translatedEn
                                ? (translatedEn.slice(0, 45) + (translatedEn.length > 45 ? '\u2026' : ''))
                                : '\u2014'}
                            </td>
                            <td style={{ textAlign: 'center' }}><SentimentBadge sentiment={row.sentiment} confidence={row.confidence} showConfidence={false} /></td>
                            <td className="col-num" style={{ textAlign: 'center' }}>{row.confidence.toFixed(1)}%</td>
                            {bRunSarcasm && (
                              <td className="col-num" style={{ textAlign: 'center' }}>
                                {row.sarcasm_detected ? <span className="sarcasm-warn">!!</span> : '\u2014'}
                              </td>
                            )}
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
                {bResult.results && <AnalysisErrorSummary results={bResult.results} />}
              </div>

              {/* Charts */}
              <div className="chart-row" style={{ marginTop: 'var(--space-4)' }}>
                <div className="card animate-in">
                  <SectionHeader icon={<Icon3DChart size={22} />} title="Sentiment Distribution" subtitle="Proportion of sentiments across reviews" />
                  <div className="card-body">
                    <SentimentPieChart
                      positive={bResult.summary.positive_pct}
                      negative={bResult.summary.negative_pct}
                      neutral={bResult.summary.neutral_pct} />
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
                <SectionHeader icon={<Icon3DTrend size={22} />} title="Sentiment Trend" subtitle="Batch processing sentiment distribution" />
                <div className="card-body">
                  <SentimentTrendChart data={trendPoints.length > 0 ? trendPoints : bTrendData} />
                </div>
              </div>

              {/* ABSA Aggregation — only when bRunAbsa was enabled and data returned */}
              {bRunAbsa && bTopAbsaAspects.length > 0 && (
                <div className="card animate-in card--animated" style={{ marginTop: 'var(--space-4)' }}>
                  <SectionHeader icon={<Icon3DTarget size={22} />} title="Aspect-Based Sentiment Analysis" subtitle={`Top ${bTopAbsaAspects.length} aspects across ${bResult?.summary?.total_analyzed ?? 0} reviews`} />
                  <div className="card-body">
                    <table className="absa-table">
                      <thead><tr>
                        <th>Aspect</th>
                        <th>Mentions</th>
                        <th>Dominant</th>
                        <th>Positive</th>
                        <th>Negative</th>
                        <th>Neutral</th>
                        <th>Avg Polarity</th>
                      </tr></thead>
                      <tbody>
                        {bTopAbsaAspects.map(a => (
                          <tr key={a.aspect}>
                            <td style={{ textAlign: 'center', fontWeight: 600, textTransform: 'capitalize' }}>{a.aspect}</td>
                            <td style={{ textAlign: 'center' }}>{a.count}</td>
                            <td style={{ textAlign: 'center' }}>
                              <span className={`badge badge-${a.dominantSentiment}`} style={{ fontSize: '10px', textTransform: 'capitalize' }}>{a.dominantSentiment}</span>
                            </td>
                            <td style={{ textAlign: 'center', color: 'var(--color-positive)' }}>{a.positive}</td>
                            <td style={{ textAlign: 'center', color: 'var(--color-negative)' }}>{a.negative}</td>
                            <td style={{ textAlign: 'center', color: 'var(--color-neutral-sent)' }}>{a.neutral}</td>
                            <td style={{ textAlign: 'center', fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)' }}>{a.avgPolarity.toFixed(3)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}

              {bRunSarcasm && (
                <div className="card animate-in card--animated" style={{ marginTop: 'var(--space-4)' }}>
                  <SectionHeader icon={<Icon3DSarcasm size={22} />} title="Sarcasm Detection Summary" subtitle="Dataset-level sarcasm analysis" />
                  <div className="card-body">
                    {(bResult?.summary?.sarcasm_count ?? 0) > 0 ? (
                      <div style={{
                        display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--space-3)',
                        padding: 'var(--space-4)',
                      }}>
                        <div style={{
                          display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--space-2)',
                          padding: 'var(--space-4) var(--space-6)',
                          background: 'rgba(244,63,94,0.08)',
                          border: '1px solid rgba(244,63,94,0.25)',
                          borderRadius: '12px',
                          textAlign: 'center',
                        }}>
                          <svg width="36" height="36" viewBox="0 0 48 48" style={icon3dStyle} fill="none">
                            <defs><linearGradient id="lsarc-warn" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#F43F5E"/><stop offset="100%" stopColor="#FDE047"/></linearGradient></defs>
                            <path d="M24 6L44 40H4z" stroke="url(#lsarc-warn)" strokeWidth="2" fill="url(#lsarc-warn)" fillOpacity=".12" strokeLinejoin="round"/>
                            <path d="M24 18v10M24 33v2" stroke="url(#lsarc-warn)" strokeWidth="2.5" strokeLinecap="round"/>
                          </svg>
                          <div style={{ fontSize: 'var(--text-lg)', fontWeight: 700, color: 'var(--color-negative)' }}>
                            {bResult.summary.sarcasm_count} review{bResult.summary.sarcasm_count !== 1 ? 's' : ''} detected as sarcastic
                          </div>
                          <div style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)' }}>
                            {bResult.summary.total_analyzed > 0
                              ? `${((bResult.summary.sarcasm_count / bResult.summary.total_analyzed) * 100).toFixed(1)}% of the dataset — these reviews may mislead sentiment analysis`
                              : 'Sarcasm detected in this dataset'}
                          </div>
                        </div>
                        <div style={{ fontSize: 'var(--text-xs)', color: 'var(--color-text-faint)', textAlign: 'center', maxWidth: '480px' }}>
                          Sarcastic reviews are flagged by the <strong>!! indicator</strong> in the results table above. Consider excluding or re-weighting them for downstream tasks.
                        </div>
                      </div>
                    ) : (
                      <div style={{
                        display: 'flex', flexDirection: 'column', alignItems: 'center',
                        padding: 'var(--space-5)',
                      }}>
                        <div style={{
                          display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--space-2)',
                          padding: 'var(--space-4) var(--space-6)',
                          background: 'rgba(34,197,94,0.08)',
                          border: '1px solid rgba(34,197,94,0.2)',
                          borderRadius: '12px',
                          textAlign: 'center',
                        }}>
                          <svg width="36" height="36" viewBox="0 0 48 48" style={icon3dStyle} fill="none">
                            <defs><linearGradient id="lsarc-ok" x1="0" y1="0" x2="48" y2="48"><stop offset="0%" stopColor="#22C55E"/><stop offset="100%" stopColor="#2DD4BF"/></linearGradient></defs>
                            <circle cx="24" cy="24" r="18" stroke="url(#lsarc-ok)" strokeWidth="2" fill="url(#lsarc-ok)" fillOpacity=".1"/>
                            <path d="M14 24l8 8 12-14" stroke="url(#lsarc-ok)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
                          </svg>
                          <div style={{ fontSize: 'var(--text-lg)', fontWeight: 700, color: 'var(--color-positive)' }}>
                            No Sarcasm Detected
                          </div>
                          <div style={{ fontSize: 'var(--text-sm)', color: 'var(--color-text-muted)' }}>
                            All processed reviews show consistent linguistic patterns — sentiment predictions are stable and reliable.
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* AI Summary */}
              <div className="card animate-in" style={{ marginTop: 'var(--space-4)' }}>
                <SectionHeader icon={<Icon3DAI size={22} />} title="AI Summary" subtitle="Intelligent analysis synopsis" />
                <div className="ai-summary" style={{ textAlign: 'center' }}>
                  <div className="ai-summary__item" style={{ justifyContent: 'flex-start', textAlign: 'left' }}>
                    <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}><Icon3DTotal size={16} /></span>
                    <span><strong>Overall:</strong> {bResult.summary.total_analyzed} reviews analyzed with multilingual support.</span>
                  </div>
                  <div className="ai-summary__item" style={{ justifyContent: 'flex-start', textAlign: 'left' }}>
                    <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}><Icon3DChart size={16} /></span>
                    <span><strong>Distribution:</strong> {bResult.summary.positive_pct}% positive, {bResult.summary.negative_pct}% negative, {bResult.summary.neutral_pct}% neutral.</span>
                  </div>
                  <div className="ai-summary__item" style={{ justifyContent: 'flex-start', textAlign: 'left' }}>
                    <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}><Icon3DGlobe size={16} /></span>
                    <span><strong>Language Diversity:</strong> {bLanguageCount} language{bLanguageCount > 1 ? 's' : ''} detected. Primary: English.</span>
                  </div>
                  <div className="ai-summary__item" style={{ justifyContent: 'flex-start', textAlign: 'left' }}>
                    <span className="ai-summary__icon" style={{ display: 'inline-flex', alignItems: 'center' }}><Icon3DSentiment size={16} /></span>
                    <span><strong>Sarcasm:</strong> {bResult.summary.sarcasm_count} reviews flagged as sarcastic.</span>
                  </div>
                </div>
              </div>

              {/* Export */}
              <div className="card animate-in card--animated" style={{ marginTop: 'var(--space-4)' }}>
                <SectionHeader icon={<Icon3DExport size={22} />} title="Export Results" subtitle="Download analysis in multiple formats" />
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 'var(--space-3)', padding: 'var(--space-4)' }}>
                  <NeuralButton variant="secondary" size="sm" style={{ width: '100%', justifyContent: 'center' }} onClick={() => {
                    if (!bResult?.results) return
                    generateUniversalCSV({
                      rows: bResult.results,
                      mode: 'language',
                      filename: 'language-batch.csv',
                      absaAspects: bRunAbsa ? bTopAbsaAspects : undefined,
                      sarcasmEnabled: bRunSarcasm,
                      sarcasmCount: bResult.summary?.sarcasm_count,
                    })
                    showToast('success', 'CSV exported successfully')
                  }}>📄 CSV</NeuralButton>
                  <NeuralButton variant="secondary" size="sm" style={{ width: '100%', justifyContent: 'center' }} onClick={() => {
                    if (!bResult?.results || !bResult.summary) return
                    generateUniversalPDF({
                      title: 'ReviewSense Analytics',
                      subtitle: `Multilingual Bulk Analysis Report — ${bResult.summary.total_analyzed} Reviews`,
                      rows: bResult.results,
                      summary: bResult.summary,
                      mode: 'language',
                      topKeywords: bTopKeywords,
                      filename: 'language-batch.html',
                      absaAspects: bRunAbsa ? bTopAbsaAspects : undefined,
                      sarcasmEnabled: bRunSarcasm,
                    })
                    showToast('success', 'PDF report exported successfully')
                  }}>📑 PDF</NeuralButton>
                  <NeuralButton variant="secondary" size="sm" style={{ width: '100%', justifyContent: 'center' }} onClick={() => {
                    if (!bResult?.results || !bResult.summary) return
                    generateUniversalJSON({
                      rows: bResult.results,
                      summary: bResult.summary,
                      mode: 'language',
                      filename: 'language-batch.json',
                      absaAspects: bRunAbsa ? bTopAbsaAspects : undefined,
                      sarcasmEnabled: bRunSarcasm,
                    })
                    showToast('success', 'JSON exported successfully')
                  }}>{'{ }'} JSON</NeuralButton>
                  <NeuralButton variant="secondary" size="sm" style={{ width: '100%', justifyContent: 'center' }} onClick={() => {
                    if (!bResult?.results) return
                    generateUniversalExcel({
                      rows: bResult.results,
                      mode: 'language',
                      filename: 'language-batch.xls',
                      absaAspects: bRunAbsa ? bTopAbsaAspects : undefined,
                      sarcasmEnabled: bRunSarcasm,
                      sarcasmCount: bResult.summary?.sarcasm_count,
                    })
                    showToast('success', 'Excel exported successfully')
                  }}>📊 Excel</NeuralButton>
                </div>

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
