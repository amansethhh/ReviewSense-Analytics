# ReviewSense Analytics

> **Production-grade, multi-domain sentiment analysis system built with Python and Streamlit.**

---

## Overview

ReviewSense Analytics is a full-stack machine-learning project that classifies customer reviews across five domains — food products, movies, airlines, Indian e-commerce, and social media — into **Negative / Neutral / Positive** sentiments. It combines classical ML models with a fine-tuned RoBERTa transformer, and wraps everything in an interactive dark-themed Streamlit dashboard.

---

## Key Features

| Feature | Description |
|---|---|
| 🎯 **Multi-Domain Sentiment** | Trained on 1.3 M reviews across 5 domains |
| 🤖 **Classical ML Pipeline** | Naive Bayes · LinearSVC · Logistic Regression · Random Forest with TF-IDF |
| 🧠 **RoBERTa Fine-Tuning** | Domain-adapted transformer for high-accuracy inference |
| 🔍 **Explainable AI (LIME)** | Token-level explanations for every prediction |
| 🏷️ **ABSA** | Aspect-Based Sentiment Analysis using spaCy |
| 🌍 **Multilingual** | Language detection + auto-translation via googletrans |
| 😏 **Sarcasm Detection** | Flags sarcastic reviews to prevent mis-classification |
| 📄 **PDF Export** | One-click professional report generation with fpdf2 |
| 📊 **Interactive Dashboard** | Plotly charts, confusion matrices, word clouds |

---

## Project Structure

```
ReviewSense-Analytics/
├── data/
│   ├── processed/          # Dataset (gitignored — copy CSV here)
│   └── exports/            # Generated export files
├── models/
│   ├── classical/          # Saved sklearn models + vectoriser
│   └── roberta/            # Fine-tuned RoBERTa checkpoints
├── notebooks/              # Exploratory notebooks
├── src/
│   ├── config.py           # Project-wide constants
│   ├── preprocess.py       # Data cleaning & splitting
│   ├── train_classical.py  # Classical model training
│   ├── evaluate.py         # Evaluation & metrics
│   ├── predict.py          # Inference helpers
│   ├── absa.py             # Aspect-Based Sentiment Analysis
│   ├── lime_explainer.py   # LIME explanation wrapper
│   ├── summarizer.py       # Extractive review summarisation
│   ├── sarcasm_detector.py # Sarcasm detection
│   ├── translator.py       # Language detection & translation
│   └── pdf_exporter.py     # PDF report generation
├── app/
│   ├── app.py              # Streamlit entry point
│   ├── pages/
│   │   ├── 01_Live_Prediction.py
│   │   ├── 02_Bulk_Analysis.py
│   │   ├── 03_Model_Dashboard.py
│   │   └── 04_Language_Analysis.py
│   └── assets/
│       └── style.css       # Glassmorphism dark theme
├── reports/figures/        # Saved plots & figures
├── colab/                  # Google Colab training notebooks
├── requirements.txt
└── README.md
```

---

## Quick Start

```bash
# 1. Clone & install dependencies
git clone https://github.com/amansethhh/ReviewSense-Analytics.git
cd ReviewSense-Analytics
pip install -r requirements.txt

# 2a. Quick demo — generate sample model artifacts (no dataset needed)
python scripts/generate_demo_artifacts.py

# 2b. OR: place the full dataset and train production models
#    Copy reviewsense_dataset.csv → data/processed/
python src/preprocess.py
python src/train_classical.py

# 3. Launch the dashboard
streamlit run app/app.py
```

---

## Tech Stack

**ML / NLP:** scikit-learn · XGBoost · Hugging Face Transformers (RoBERTa) · NLTK · spaCy · TextBlob · LIME · sumy  
**App:** Streamlit · Plotly · Matplotlib · Seaborn · WordCloud  
**Utilities:** pandas · NumPy · joblib · tqdm · langdetect · googletrans · fpdf2 · openpyxl

---

## Dataset

The dataset (`reviewsense_dataset.csv`, ~1.3 M rows) is **not** included in this repository due to size constraints.  
Place the file at `data/processed/reviewsense_dataset.csv` before running preprocessing.

---

## License

[MIT](LICENSE)

