# ReviewSense Analytics

AI-powered sentiment analysis platform combining classical ML classifiers with RoBERTa transformer-based NLP. Supports single review prediction with LIME explainability, aspect-based sentiment analysis (ABSA), sarcasm detection, multilingual support for 15+ languages, and bulk CSV processing with background job polling.

ReviewSense Analytics uses a decoupled architecture: a FastAPI backend wraps the existing ML pipeline (`src/`) and exposes it as a REST API, while a React + Vite frontend provides a modern, responsive UI that consumes these endpoints.

## Architecture Overview

```
Browser (React / Vite :5173)
    │  HTTP / JSON
    ▼
FastAPI Backend (:8000)
    │  Python import
    ▼
src/ (ML Pipeline)
    ├── predict.py    ─ RoBERTa sentiment + 4 classifiers
    ├── absa.py       ─ Aspect-Based Sentiment Analysis
    ├── sarcasm.py    ─ Irony / sarcasm detection
    ├── translator.py ─ Language detection + MarianMT
    └── train.py      ─ Model training + metrics
```

## Local Development

### Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- Trained model files in `models/` directory

### 1. Start the Backend

```bash
cd ReviewSense-Analytics
pip install -r requirements.txt
uvicorn backend.app.main:app --reload --port 8000
```

Verify: `http://localhost:8000/health` should return `{"status": "ok", "models_loaded": true}`

### 2. Start the Frontend

```bash
cd ReviewSense-Analytics/frontend
npm install
npm run dev
```

Open: `http://localhost:5173`

### 3. Run Parity Validation

```bash
python backend/tests/validate_parity.py
```

Expected: `✅ PHASE 1 COMPLETE — All 20 tests passed`

## Deployment

### Backend (Render)

1. Push to GitHub
2. Connect to [Render](https://render.com)
3. Use the `render.yaml` blueprint for auto-configuration
4. Set runtime to Python 3.10
5. The health check path is `/health`

### Frontend (Vercel / Netlify / Cloudflare Pages)

1. Set build command: `cd frontend && npm install && npm run build`
2. Set output directory: `frontend/dist`
3. Set `VITE_API_URL` environment variable to your backend URL
4. SPA routing is handled by `vercel.json`, `_redirects`, or `404.html`

## API Reference

| Method | Path                  | Description                                  |
|--------|-----------------------|----------------------------------------------|
| POST   | `/predict`            | Single review sentiment analysis             |
| POST   | `/bulk`               | Submit bulk CSV for background processing    |
| GET    | `/bulk/status/{id}`   | Poll bulk job progress and results           |
| POST   | `/bulk/columns`       | Preview CSV columns and first rows           |
| POST   | `/language`           | Language detection + translation + sentiment |
| GET    | `/metrics`            | Model performance metrics and confusion data |
| GET    | `/health`             | Backend health check                         |

## Tech Stack

| Backend                    | Frontend                    |
|----------------------------|-----------------------------|
| Python 3.10                | React 18 + TypeScript       |
| FastAPI + Uvicorn          | Vite 5                      |
| RoBERTa (Transformers)     | Recharts                    |
| scikit-learn (4 classifiers)| React Router DOM           |
| TextBlob + NLTK            | Context + useReducer        |
| MarianMT (Translation)     | Hand-written CSS (dark mode)|
| LIME (Explainability)      | No CSS frameworks           |

## License

This project is built for educational and portfolio purposes.
