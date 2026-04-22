import { useNavigate } from 'react-router-dom'
import { NeuralButton } from '@/components/ui/NeuralButton'
import { PageWrapper } from '@/components/layout/PageWrapper'
import { EyebrowPill } from '@/components/ui/EyebrowPill'
import { TypingText } from '@/components/ui/TypingText'
import { useApp } from '@/context/AppContext'
import {
  PredictIcon,
  LanguageIcon,
  BulkIcon,
  DashboardIcon,
  SparkleIcon,
} from '@/components/icons/NavIcons'
import type { FC } from 'react'

interface FeatureCard {
  Icon:  FC<{ className?: string; size?: number }>
  title: string
  desc:  string
  path:  string
  tags:  { label: string; cls: string }[]
}

const FEATURE_CARDS: FeatureCard[] = [
  {
    Icon: PredictIcon,
    title: 'Real-Time Prediction',
    desc: 'Analyze any review with RoBERTa transformer — sentiment, confidence, LIME explainability, ABSA, and sarcasm detection.',
    path: '/predict',
    tags: [
      { label: 'LIVE', cls: 'ai-tag--ai' },
      { label: 'LOW LATENCY', cls: 'ai-tag--instant' },
      { label: 'REST API', cls: '' },
    ],
  },
  {
    Icon: LanguageIcon,
    title: 'Multi-Language Support',
    desc: 'Auto-detect language, translate to English, and run sentiment analysis. Supports 50+ languages including Hindi, German, Spanish.',
    path: '/language',
    tags: [
      { label: '50+ LANGUAGES', cls: 'ai-tag--ai' },
      { label: 'AUTO-DETECT', cls: 'ai-tag--instant' },
      { label: 'XLM-R', cls: '' },
    ],
  },
  {
    Icon: BulkIcon,
    title: 'Bulk Analysis Pipeline',
    desc: 'Upload a CSV of thousands of reviews. Background processing with live progress polling — no timeouts, no page locks.',
    path: '/bulk',
    tags: [
      { label: 'CSV UPLOAD', cls: 'ai-tag--ai' },
      { label: 'BATCH MODE', cls: 'ai-tag--instant' },
      { label: 'REPORTS', cls: '' },
    ],
  },
  {
    Icon: DashboardIcon,
    title: 'Model Explainability',
    desc: 'Compare all 4 classifiers on accuracy, F1 scores, AUC, training time, and full confusion matrices.',
    path: '/dashboard',
    tags: [
      { label: 'LIME', cls: 'ai-tag--ai' },
      { label: 'SHAP', cls: 'ai-tag--instant' },
      { label: 'ATTENTION MAPS', cls: '' },
    ],
  },
]

export function HomePage() {
  const navigate = useNavigate()
  const { state } = useApp()

  return (
    <PageWrapper
      title="ReviewSense Analytics"
      subtitle="Sentiment intelligence powered by RoBERTa"
      hideTopBar
    >
      {/* Hero */}
      <section className="home-hero">
        <EyebrowPill variant="sentiment-engine">
          <SparkleIcon className="heading-icon" size={14} />
          AI-POWERED SENTIMENT ENGINE
        </EyebrowPill>
        <h2 className="home-hero__title">
          <span className="home-hero__gradient-text">ReviewSense</span>{' '}<TypingText />
        </h2>
        <p className="home-hero__subtitle">
          Advanced sentiment analysis powered by transformer-based NLP models.
          Real-time predictions, multi-language support, and deep
          explainability — all in one platform.
        </p>
        <div className="home-hero__ctas">
          <NeuralButton variant="gradient" size="lg" icon="arrow" onClick={() => navigate('/predict')}>
            Get Started
          </NeuralButton>
          <NeuralButton variant="secondary" size="lg" icon="dashboard" onClick={() => navigate('/dashboard')}>
            View Dashboard
          </NeuralButton>
        </div>
      </section>

      {/* KPI Cards */}
      <section>
        <div className="kpi-grid" style={{ gridTemplateColumns: 'repeat(4,1fr)' }}>
          <div className="card kpi-card kpi-card--total">
            <div className="kpi-card__tag">Total Reviews Analyzed</div>
            <div className="kpi-card__value">1.2M+</div>
            <div className="kpi-card__sub" style={{ color: 'var(--color-positive)' }}>+23.5%</div>
          </div>
          <div className="card kpi-card kpi-card--positive">
            <div className="kpi-card__tag">Model Accuracy</div>
            <div className="kpi-card__value">95.8%</div>
            <div className="kpi-card__sub">+3.2%</div>
          </div>
          <div className="card kpi-card kpi-card--negative">
            <div className="kpi-card__tag">Avg. Latency</div>
            <div className="kpi-card__value" style={{ color: '#f43f5e' }}>42ms</div>
            <div className="kpi-card__sub" style={{ color: 'var(--color-positive)' }}>-15.3%</div>
          </div>
          <div className="card kpi-card kpi-card--neutral">
            <div className="kpi-card__tag">Positive Sentiment</div>
            <div className="kpi-card__value">78.2%</div>
            <div className="kpi-card__sub" style={{ color: 'var(--color-positive)' }}>+5.8%</div>
          </div>
        </div>
      </section>

      {/* Feature cards — 2×2 grid */}
      <section className="home-features" style={{ marginTop: 'var(--space-8)' }}>
        <h2 className="section-title" style={{ display: 'inline-flex', alignItems: 'center', gap: '8px' }}>
          <SparkleIcon className="heading-icon" size={20} />
          Core Capabilities
        </h2>
        <div className="features-grid">
          {FEATURE_CARDS.map(f => (
            <div key={f.path} className="feature-card card"
                 onClick={() => navigate(f.path)}
                 role="button" tabIndex={0}
                 onKeyDown={e => e.key === 'Enter' &&
                   navigate(f.path)}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                <span className="feature-icon-wrap" style={{ marginBottom: 0 }}>
                  <f.Icon className="nav-icon" size={26} />
                </span>
                <h3 className="feature-card__title" style={{ margin: 0 }}>
                  {f.title}
                </h3>
              </div>
              <p className="feature-card__desc">{f.desc}</p>
              <div className="feature-card__tags">
                {f.tags.map(t => (
                  <span key={t.label} className={`ai-tag ${t.cls}`}>
                    {t.label}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Status strip */}
      <section style={{ marginTop: 'var(--space-6)' }}>
        <div className="card status-strip">
          <div className="status-strip__item">
            <span className={`status-dot${
              state.apiConnected ? '' : ' status-dot--offline'
            }`} />
            {state.apiConnected ? 'Backend Online' : 'Backend Offline'}
          </div>
          <div className="status-strip__item">
            RoBERTa Transformer · 95.8% accuracy
          </div>
          <div className="status-strip__item">
            v1.0.0
          </div>
        </div>
      </section>
    </PageWrapper>
  )
}
