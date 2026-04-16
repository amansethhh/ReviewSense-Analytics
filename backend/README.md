# ReviewSense Analytics — FastAPI Backend

## Setup

```bash
cd ReviewSense-Analytics
pip install -r backend/requirements.txt
```

## Run

```bash
# From project root (important for src/ imports)
uvicorn backend.app.main:app --reload --port 8000
```

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | / | Health check |
| GET | /health | Models loaded status |
| POST | /predict | Single review analysis |
| POST | /bulk | Submit CSV bulk job |
| GET | /bulk/status/{job_id} | Poll bulk job |
| GET | /bulk/columns | Preview CSV columns |
| POST | /language | Language detect + analyze |
| GET | /metrics | All model metrics |
| GET | /docs | Swagger UI |

## Test

```bash
pytest backend/tests/ -v
```

## Phase 1 Validation — 20 Test Inputs

Run this to validate API outputs match Streamlit:

```bash
python backend/tests/validate_parity.py
```
