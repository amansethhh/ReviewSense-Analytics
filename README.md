<div align="center">

<img src="docs/images/logo.png" width="140"/>

# ReviewSense Analytics

<p align="center">
 Production-ready multilingual sentiment intelligence platform
</p>

<p align="center">
 Hybrid Transformer Routing • Confidence-Aware Decisions • Explainable AI
</p>

<br>

<p>
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/React-18-61DAFB?logo=react&logoColor=black"/>
  <img src="https://img.shields.io/badge/Transformers-HuggingFace-FFD21E"/>
  <img src="https://img.shields.io/badge/License-MIT-green.svg"/>
</p>

<p align="center">
  ⭐ If you like this project, consider giving it a star!
</p>

</div>

---

## 🎬 Live Demo

<p align="center">

<img 
  src="https://raw.githubusercontent.com/amansethhh/ReviewSense-Analytics/main/docs/images/demo-preview.gif"
  alt="ReviewSense Demo"
  width="900"
/>

</p>

<p align="center">
<sub>Real-time multilingual sentiment analysis • Bulk CSV processing • Explainability • Interactive dashboard</sub>
</p>

---

## 🌍 Why This Matters

* Businesses receive **multilingual, mixed-language feedback daily**
* Traditional models fail on **code-switched (Hinglish) inputs**
* Translation errors silently degrade prediction quality
* Incorrect sentiment → **wrong business decisions**

**ReviewSense solves this with reliable, explainable, multilingual intelligence**

---

## ⚡ Key Highlights

* Hybrid transformer routing (RoBERTa + XLM-R + NLLB)
* Hinglish normalization for real-world inputs
* Translation trust validation (fail-safe fallback)
* Margin-based decision layer (ambiguity control)
* Entropy-based confidence calibration
* Explainability via LIME + ABSA
* Real-time + bulk processing pipeline

---

## 🧩 Use Cases

* E-commerce product review analysis
* Social media sentiment monitoring
* Multilingual customer feedback systems
* Market research & brand intelligence

---

## 🎯 Problem

* Multilingual input breaks traditional models
* Translation introduces hidden errors
* Confidence scores are misleading
* Ambiguous predictions are mishandled
* Lack of explainability

---

## 💡 Solution Overview

<div align="center">

| Layer                  | Purpose                                  |
| ---------------------- | ---------------------------------------- |
| Language Routing       | Detect English / Hinglish / Multilingual |
| Hinglish Normalization | Clean code-mixed input                   |
| Translation (NLLB)     | Convert multilingual → English           |
| Validation Layer       | Verify translation quality               |
| Model Layer            | RoBERTa / XLM-R inference                |
| Decision Layer         | Margin-based ambiguity handling          |
| Confidence Layer       | Entropy calibration                      |
| Explainability         | LIME + ABSA                              |

</div>

---

## 🧠 Core Innovations

* Model-first architecture (no heuristics)
* Margin-based ambiguity detection
* Entropy-based confidence (not softmax)
* Translation trust gating system

---

## 🧩 Architecture Diagram

<div align="center">

<img src="docs/images/your-architecture.png" width="900"/>

</div>

---

## 📊 Performance

<div align="center">

<table>
<tr><th>Metric</th><th>Value</th></tr>
<tr><td>Accuracy</td><td>~91%</td></tr>
<tr><td>Precision</td><td>~0.92</td></tr>
<tr><td>Recall</td><td>~0.91</td></tr>
<tr><td>F1 Score</td><td>~0.90</td></tr>
</table>

<p><sub>Evaluated on mixed multilingual dataset (real-world inputs)</sub></p>

</div>

---

## 🖼️ UI Preview

<div align="center">

<table>
<tr>
<td align="center"><img src="docs/images/home.png" width="400"/><br/>Home</td>
<td align="center"><img src="docs/images/live_prediction.png" width="400"/><br/>Live Prediction</td>
</tr>
<tr>
<td align="center"><img src="docs/images/model_dashboard.png" width="400"/><br/>Model Dashboard</td>
<td align="center"><img src="docs/images/multilingual_analysis.png" width="400"/><br/>Multilingual Analysis</td>
</tr>
</table>

</div>

---

## 🏗️ Tech Stack

<div align="center">

| Layer          | Technology            |
| -------------- | --------------------- |
| Backend        | FastAPI, Uvicorn      |
| Frontend       | React, TypeScript     |
| Models         | RoBERTa, XLM-R        |
| Translation    | Meta NLLB             |
| Explainability | LIME, ABSA            |
| ML Stack       | PyTorch, Transformers |
| Data           | Pandas, NumPy         |

</div>

---

## 📂 Project Structure (Engineering-Level)

```bash
ReviewSense-Analytics/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   ├── routes/
│   │   ├── services/
│   │   ├── schemas/
│   │   ├── core/
│   │   └── utils/
│   └── tests/
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   ├── pages/
│   │   ├── hooks/
│   │   ├── services/
│   │   └── styles/
│
├── src/
│   ├── models/
│   ├── pipeline/
│   ├── preprocessing/
│   ├── translation/
│   ├── decision/
│   └── predict.py
│
├── docs/
│   └── images/
│
├── scripts/
├── reports/
├── data/
└── start.ps1
```

---

## 🔌 API Overview

<div align="center">

| Method | Endpoint  | Description         |
| ------ | --------- | ------------------- |
| GET    | /health   | Health check        |
| POST   | /predict  | Real-time sentiment |
| POST   | /bulk     | Bulk CSV processing |
| GET    | /metrics  | Model metrics       |
| POST   | /feedback | Feedback logging    |

</div>

---

## 🛠 Setup Instructions

### 🔧 Prerequisites

Ensure your system has:

- Python **3.10+**
- Node.js **18+**
- npm or yarn
- Git

---

## 📥 Clone Repository

```bash
git clone https://github.com/amansethhh/ReviewSense-Analytics.git
cd ReviewSense-Analytics
```
## ⚙️ Backend Setup (FastAPI)

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate environment
# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```
▶ Run Backend Server

```bash
uvicorn app.main:app --reload --port 8000
```
Backend running at:

```bash
http://localhost:8000
```
## 🌐 Frontend Setup (React + TypeScript)

```bash
cd frontend

npm install
```
▶ Run Frontend

```bash
npm run dev
```
Frontend running at:

```bash
http://localhost:5173
```
## 🔗 Environment Configuration

Create a .env file inside frontend/:

```bash
VITE_API_URL=http://localhost:8000
```
---

## 🧪 How to Use

- 🔍 **Live Prediction**  
  Enter multilingual or Hinglish text → get sentiment, confidence, explanation  

- 📦 **Bulk Analysis**  
  Upload CSV file → process batch sentiment predictions  

- 📊 **Dashboard**  
  View analytics, insights, and model outputs  
  
---

## 📁 System Flow

Input → API → NLP Pipeline → Model → Decision Layer → Output → Dashboard

---

## 📝 Notes

First run may take time due to model loading
Ensure internet connection for translation models (NLLB)
Use small datasets initially for faster testing

---

## ⚠️ Design Principles

* No heuristics
* Model-first decisions
* Deterministic outputs
* Translation-aware routing
* Fully traceable pipeline

---

## 🔮 Future Work

* Domain-specific fine-tuning
* Advanced translation scoring
* Sarcasm detection upgrade
* CI/CD + deployment pipeline

---

## 📜 License

MIT License

---

<div align="center">

Built with ❤️ by <a href="https://github.com/amansethhh">amansethhh</a>

</div>
