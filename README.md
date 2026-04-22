<![CDATA[<div align="center">

# 🚀 ReviewSense Analytics

### Production-Ready Multilingual Sentiment Intelligence Engine

A fully model-driven sentiment analysis platform built on a **Hybrid Transformer Pipeline** — combining RoBERTa, XLM-RoBERTa, and NLLB translation with margin-based decision logic, entropy-calibrated confidence, and zero heuristic overrides. Engineered for real-world multilingual review data across 30+ languages including Hinglish.

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![TypeScript](https://img.shields.io/badge/TypeScript-5-3178C6?logo=typescript&logoColor=white)](https://typescriptlang.org)
[![Transformers](https://img.shields.io/badge/🤗_Transformers-4.40+-FFD21E)](https://huggingface.co/docs/transformers)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

</div>

---

## 🎯 Problem Statement

Most sentiment analysis systems fail in production because they rely on:

- **Heuristic overrides** — TextBlob polarity and VADER compound scores silently flip transformer predictions, creating inconsistent outputs
- **Monolingual architectures** — English-only models return garbage labels for Hindi, Arabic, Japanese, and code-switched text
- **Uncalibrated confidence** — Raw softmax scores masquerade as confidence, even when the model is genuinely uncertain
- **No translation accountability** — Translated text is blindly trusted for inference, even when the translation inverts sentiment polarity
- **Hinglish blindspots** — Code-switched Hindi-English text (500M+ speakers) is misclassified as English and routed to the wrong model

ReviewSense Analytics was built to solve every one of these problems with a deterministic, model-first architecture.

---

## 💡 Solution Overview

ReviewSense replaces heuristic sentiment pipelines with a **Hybrid Transformer Pipeline** that makes every decision traceable and deterministic:

| Layer | What It Does |
|---|---|
| **Language Detection** | 4-tier detection: Hinglish pre-check → Unicode script analysis → langdetect with confidence thresholding → fallback |
| **Smart Routing** | Routes English → RoBERTa, Hinglish → Normalize → RoBERTa, Multilingual → Translate → Trust Gate → RoBERTa or XLM-R |
| **Translation Validation** | NLLB translations pass through degenerate output detection, length-ratio plausibility checks, and semantic trust verification before being used for inference |
| **Margin-Based Decisions** | Instead of trusting argmax blindly, the system checks the margin between top-2 predictions. If the margin is too small, the prediction is marked ambiguous |
| **Entropy Confidence** | Confidence is derived from information-theoretic entropy, not raw softmax — a uniform distribution correctly returns low confidence |
| **Sarcasm Detection** | RoBERTa-based irony classifier with regex contradiction fallback and hedge-phrase exclusion guards |

**Zero heuristic overrides.** No TextBlob. No VADER. No polarity-based label flipping. Every output is the direct result of transformer inference.

---

## 🎬 Demo

▶ **Watch Full Demo:**
https://github.com/amansethhh/ReviewSense-Analytics/releases/download/v1.0/demo.mp4

*End-to-end walkthrough: live prediction, multilingual analysis, bulk CSV processing, model dashboard, and PDF export — all running on the Hybrid Transformer Pipeline.*

---

## ✨ Key Features

<table>
<tr>
<td width="50%">

### 🧠 Intelligence
- **Hybrid Inference** — RoBERTa (English) + XLM-R (30+ languages) with dynamic routing
- **Hinglish Normalization** — Dedicated preprocessing for code-switched Hindi-English text
- **Translation Trust Gate** — NLLB translations validated before inference; rejected translations fall back to XLM-R on original text
- **Margin-Based Decision Layer** — Dynamic thresholds per route (English: 0.06, XLM-R: 0.10, Translated: 0.08)
- **Entropy-Based Confidence** — Information-theoretic calibration replaces raw softmax

</td>
<td width="50%">

### ⚡ Production
- **Sarcasm Detection** — RoBERTa irony model + linguistic contradiction patterns with exclusion guards
- **ABSA** — Aspect-Based Sentiment Analysis with per-aspect RoBERTa scoring
- **LIME Explainability** — Feature attribution with stopword suppression and non-Latin guards
- **Bulk Processing** — Background job queue with real-time progress polling
- **PDF Export** — Branded analytical reports with full pipeline metadata

</td>
</tr>
</table>

---

## 🧠 Core Innovation

This section explains what makes ReviewSense fundamentally different from typical sentiment analysis projects.

### 1. Heuristic Elimination

Most sentiment systems layer TextBlob polarity or VADER compound scores on top of transformer predictions. This creates a hidden override: the transformer says *Positive* with 78% confidence, but TextBlob polarity is -0.2, so the system silently flips the label to *Neutral*.

**ReviewSense removed all heuristic overrides.** The transformer's softmax distribution is the only input to the decision layer. The codebase explicitly documents what was removed:

```
REMOVED (Section 8):
  ❌ TextBlob polarity
  ❌ VADER compound
  ❌ Neutral correction v2
  ❌ Label lock / confidence gate
  ❌ Polarity-based corrections
```

### 2. Margin-Based Decision Layer

Instead of blindly trusting `argmax`, the system computes the margin between the top-2 softmax probabilities. If the margin falls below a route-specific threshold, the prediction is classified as *ambiguous* and defaulted to Neutral — preventing false-confident predictions.

```
Margin Thresholds:
  English (RoBERTa):      0.06  — well-calibrated model, tight threshold
  Hinglish (normalized):  0.06  — normalized text, same as English
  Multilingual (XLM-R):   0.10  — noisier model, looser threshold
  Translated (RoBERTa):   0.08  — translation adds noise
```

### 3. Entropy-Based Confidence Calibration

Raw softmax confidence is unreliable — a model can output `[0.34, 0.33, 0.33]` and still report 34% confidence via argmax. ReviewSense computes normalized entropy across the full probability distribution:

```python
entropy = -Σ(p * log(p))
confidence = 1 - (entropy / max_entropy)
```

Low entropy = model is sure. High entropy = model is confused. This produces confidence scores that actually mean something.

### 4. Translation Trust Gating

For non-Latin languages, the pipeline translates via NLLB (`facebook/nllb-200-distilled-600M`) — but **never trusts translation blindly**:

1. **Degenerate output detection** — catches "bad experience.", "error.", empty strings
2. **Length-ratio plausibility** — rejects translations where `len(translated) / len(original)` falls outside `[0.3, 4.0]`
3. **Semantic trust check** — validates that translation preserves the original's sentiment signal
4. **Retry logic** — on failure, pads input and retries once before falling back

If translation fails any check, the system routes to **XLM-R on original text** instead — never producing a garbage prediction from a bad translation.

---

## ⚙️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    INPUT TEXT                                │
└───────────────────────┬─────────────────────────────────────┘
                        │
                        ▼
            ┌───────────────────────┐
            │  Language Detection   │  4-tier: Hinglish → Unicode
            │  (XLM-R + langdetect) │  → langdetect → fallback
            └───────────┬───────────┘
                        │
           ┌────────────┼────────────┐
           ▼            ▼            ▼
      ┌─────────┐ ┌──────────┐ ┌──────────────┐
      │ ENGLISH │ │ HINGLISH │ │ MULTILINGUAL │
      └────┬────┘ └────┬─────┘ └──────┬───────┘
           │           │              │
           │      Normalize      ┌────┴────┐
           │      Hinglish       │ NLLB    │
           │           │         │Translate │
           │           │         └────┬────┘
           │           │              │
           │           │    ┌─────────┴─────────┐
           │           │    ▼                   ▼
           │           │  Trust ✅           Trust ❌
           │           │  RoBERTa on         XLM-R on
           │           │  translated         original
           │           │         │              │
           ▼           ▼         ▼              ▼
      ┌──────────────────────────────────────────────┐
      │         Sentiment Prediction                  │
      │  cardiffnlp/twitter-roberta-base-sentiment    │
      │  cardiffnlp/twitter-xlm-roberta-base-sent.   │
      └───────────────────┬──────────────────────────┘
                          │
                          ▼
      ┌──────────────────────────────────────────────┐
      │          Decision Layer                       │
      │  • Margin-based ambiguity detection           │
      │  • Short-text keyword guard (safety net)      │
      │  • Entropy-based confidence calibration       │
      └───────────────────┬──────────────────────────┘
                          │
                          ▼
      ┌──────────────────────────────────────────────┐
      │          Optional Enrichment                  │
      │  • Sarcasm detection (RoBERTa irony model)    │
      │  • ABSA (per-aspect RoBERTa scoring)          │
      │  • LIME explainability                        │
      └───────────────────┬──────────────────────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │  FINAL OUTPUT   │
                 │  label, conf,   │
                 │  margin, trace  │
                 └─────────────────┘
```

---

## 📊 Model Performance

Evaluated on multilingual and real-world review datasets:

| Metric | Hybrid Pipeline |
|---|---|
| **Accuracy** | 95.8% |
| **Decision Layer** | Entropy + Margin based |
| **Languages Supported** | 30+ (including Hinglish) |
| **Translation Engine** | NLLB (facebook/nllb-200-distilled-600M) |

### Benchmark Models (Offline Evaluation Only)

| Model | Accuracy | Precision | Recall | F1 |
|---|---|---|---|---|
| Naive Bayes | 88.6% | 90.0% | 87.9% | 88.3% |
| LinearSVC | 85.7% | 86.7% | 85.3% | 85.7% |
| Logistic Regression | 85.7% | 86.7% | 85.3% | 85.7% |
| Random Forest | 74.3% | 81.9% | 73.7% | 71.3% |

> ⚠️ *Classical models are used for offline benchmarking only. Production inference exclusively uses the Hybrid Transformer Pipeline (RoBERTa + XLM-R + NLLB).*

---

## 🖼️ Screenshots

<table>
<tr>
<td align="center"><img src="docs/images/home.png" width="400"/><br/><b>Home</b></td>
<td align="center"><img src="docs/images/live_prediction.png" width="400"/><br/><b>Live Prediction</b></td>
</tr>
<tr>
<td align="center"><img src="docs/images/bulk_analysis.png" width="400"/><br/><b>Bulk Analysis</b></td>
<td align="center"><img src="docs/images/model_dashboard.png" width="400"/><br/><b>Model Dashboard</b></td>
</tr>
<tr>
<td align="center" colspan="2"><img src="docs/images/language_analysis_updated.png" width="400"/><br/><b>Multilingual Analysis</b></td>
</tr>
</table>

---

## 🏗️ Tech Stack

| Layer | Technology |
|---|---|
| **Sentiment Models** | `cardiffnlp/twitter-roberta-base-sentiment-latest` (English), `cardiffnlp/twitter-xlm-roberta-base-sentiment` (Multilingual) |
| **Translation** | `facebook/nllb-200-distilled-600M` (Meta NLLB) |
| **Sarcasm Detection** | `cardiffnlp/twitter-roberta-base-irony` |
| **Explainability** | LIME (Local Interpretable Model-Agnostic Explanations) |
| **Aspect Analysis** | spaCy + domain vocabulary + RoBERTa per-aspect scoring |
| **Backend** | Python 3.10, FastAPI, Uvicorn, PyTorch, Transformers |
| **Frontend** | React 18, TypeScript, Vite 5, Recharts |
| **Styling** | Hand-crafted CSS design system (Neural Dark theme) — no frameworks |
| **Classical Benchmarks** | scikit-learn (LinearSVC, Logistic Regression, Naive Bayes, Random Forest) |

---

## 📦 Project Structure

```
ReviewSense-Analytics/
│
├── backend/                    # FastAPI REST API server
│   ├── app/
│   │   ├── main.py             # Application entry point
│   │   ├── routes/             # API route handlers
│   │   │   ├── predict.py      # /predict endpoint
│   │   │   ├── bulk.py         # /bulk + job polling
│   │   │   ├── language.py     # /language endpoint
│   │   │   ├── metrics.py      # /metrics endpoint
│   │   │   └── feedback.py     # /feedback endpoint
│   │   └── utils/              # Shared utilities
│   └── tests/                  # API integration tests
│
├── frontend/                   # React + TypeScript UI
│   └── src/
│       ├── pages/              # Route-level page components
│       ├── components/         # Reusable UI components
│       ├── hooks/              # Custom React hooks
│       ├── styles/             # Design system (tokens + components)
│       └── api/                # API client layer
│
├── src/                        # Core ML pipeline
│   ├── predict.py              # Decision layer + confidence calibration
│   ├── preprocess.py           # Text preprocessing
│   ├── system_info.py          # Architecture constants (single source of truth)
│   ├── sarcasm_detector.py     # Sarcasm detection engine
│   ├── lime_explainer.py       # LIME feature attribution
│   ├── summarizer.py           # AI summary generation
│   ├── pdf_exporter.py         # Branded PDF report export
│   ├── models/
│   │   ├── sentiment.py        # RoBERTa + XLM-R dual model routing
│   │   ├── language.py         # Language detection (Unicode + langdetect)
│   │   ├── translation.py      # NLLB translation + trust validation
│   │   ├── sarcasm_model.py    # RoBERTa irony classifier
│   │   └── aspect.py           # ABSA extraction + scoring
│   └── pipeline/
│       └── inference.py        # Unified inference pipeline (single + batch)
│
├── models/                     # Saved model weights
│   ├── classical/              # sklearn benchmark models
│   └── roberta/                # Fine-tuned RoBERTa checkpoints
│
├── scripts/                    # Training + evaluation scripts
└── data/                       # Datasets + feedback logs
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- ~4GB RAM (for transformer model loading)

### Backend

```bash
# Install dependencies
cd ReviewSense-Analytics
pip install -r requirements.txt

# Start the API server
uvicorn backend.app.main:app --reload --port 8000
```

Verify: `http://localhost:8000/health` → `{"status": "healthy"}`

### Frontend

```bash
# Install dependencies
cd frontend
npm install

# Start the dev server
npm run dev
```

Open: `http://localhost:5173`

### One-Command Launch

```powershell
# Windows — starts both backend + frontend
.\start.ps1
```

---

## 🔌 API Overview

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/predict` | Single review → sentiment + confidence + LIME + ABSA + sarcasm |
| `POST` | `/bulk` | Upload CSV → background job with real-time progress polling |
| `GET` | `/bulk/status/{id}` | Poll job progress, retrieve results when complete |
| `POST` | `/language` | Multilingual analysis with full translation pipeline trace |
| `GET` | `/metrics` | Model performance metrics, confusion matrices, training stats |
| `POST` | `/feedback` | User sentiment feedback collection |
| `GET` | `/health` | Backend health check |

### Example Request

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{"text": "This product is absolutely fantastic!", "model": "best", "domain": "all", "rating": 0}'
```

### Example Response

```json
{
  "label": "positive",
  "confidence": 88.98,
  "polarity": 0.89,
  "model_used": "roberta",
  "margin": 0.7612,
  "decision_type": "confident",
  "sarcasm_detected": false,
  "pipeline_trace": {
    "route": "ENGLISH",
    "model_used": "roberta",
    "translation_used": false
  }
}
```

---

## ⚠️ Design Principles

| Principle | Implementation |
|---|---|
| **No Heuristics** | TextBlob polarity, VADER compound, and all rule-based label overrides have been removed. Every label comes from transformer inference. |
| **Fully Model-Driven** | RoBERTa and XLM-R are the only sources of sentiment predictions. Classical models exist for benchmarking only. |
| **Translation-Aware** | Translations are validated before inference. Failed translations trigger XLM-R fallback on original text — never a garbage prediction. |
| **Deterministic Outputs** | Same input always produces same output. No random sampling, no stochastic overrides. |
| **Traceable Decisions** | Every prediction includes a `pipeline_trace` with route, model used, translation status, margin, and decision type. |
| **Fail-Safe** | Degenerate translations, empty inputs, non-Latin LIME attempts, and CJK aspect extraction all have explicit guards. |

---

## 🔮 Future Improvements

- **Domain-Specific Fine-Tuning** — Adapt RoBERTa for vertical-specific review patterns (restaurants, electronics, movies)
- **Translation Quality Scoring** — Replace binary trust gate with a continuous translation quality score
- **Enhanced Sarcasm Pipeline** — Fine-tune irony model on review-domain sarcasm datasets
- **Streaming Inference** — WebSocket-based real-time prediction for live monitoring dashboards
- **CI/CD Pipeline** — Automated testing, model versioning, and deployment via GitHub Actions

---

## 📜 License

This project is licensed under the [MIT License](LICENSE).

---

<div align="center">

**Built with engineering rigor for real-world multilingual sentiment intelligence.**

*ReviewSense Analytics — from raw text to calibrated, explainable sentiment in any language.*

</div>
]]>
