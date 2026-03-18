# 🔎 ReviewSense Analytics

> **AI-powered, multi-domain sentiment intelligence platform — built with transformer-based NLP, Streamlit, and production-grade ML pipelines.**

<p align="left">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Streamlit-1.36+-FF4B4B?style=flat-square&logo=streamlit&logoColor=white" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/HuggingFace-Transformers-FFD21F?style=flat-square&logo=huggingface&logoColor=black" alt="HuggingFace"/>
  <img src="https://img.shields.io/badge/License-MIT-22c55e?style=flat-square" alt="MIT License"/>
</p>

---

## 📌 Overview

ReviewSense Analytics is a full-stack NLP platform that classifies customer reviews into **Negative / Neutral / Positive** sentiments across five domains — food products, movies, airlines, Indian e-commerce, and social media.

**The problem it solves:** Businesses receive thousands of customer reviews daily in multiple languages. Manually reading and categorizing them is not scalable. ReviewSense automates this with a transformer-based pipeline that understands context, detects sarcasm, breaks down opinions by product aspect, and presents results in an interactive dashboard.

**Key capabilities:**
- 🌍 Handles **50+ languages** with auto-detection and translation to English before analysis
- 😏 Detects **sarcasm and irony** to prevent sentiment mis-classification
- 🔬 Performs **Aspect-Based Sentiment Analysis** to identify what customers like or dislike specifically
- 🔍 Explains every prediction with **LIME** token-level feature importance
- 📂 Processes **bulk CSV/Excel datasets** with real-time progress tracking
- 📊 Compares **four classical ML models** (SVC, LR, NB, RF) with accuracy, F1, confusion matrices, and ROC curves

---

## ✨ Features

### 🔹 Core Features

| Feature | Details |
|---|---|
| ⚡ **Live Sentiment Prediction** | Type any review, get an instant Negative / Neutral / Positive classification with confidence score, polarity, and subjectivity |
| 📂 **Bulk Review Analysis** | Upload CSV or Excel (up to 200 MB), select text column, enable modules, and receive an enriched dataset with per-row sentiment |
| 🌐 **Multilingual Analysis** | Auto-detects language (langdetect), translates to English (Helsinki-NLP MarianMT + googletrans fallback), then runs the full pipeline |
| 📊 **Model Performance Dashboard** | Side-by-side comparison of LinearSVC, Logistic Regression, Naive Bayes, and Random Forest with accuracy, Macro F1, confusion matrices, ROC curves, and training times |

### 🔹 Advanced Features

| Feature | Details |
|---|---|
| 🔬 **Aspect-Based Sentiment Analysis (ABSA)** | Extracts noun-phrase aspects with spaCy and scores each with RoBERTa polarity |
| 😏 **Sarcasm Detection** | `cardiffnlp/twitter-roberta-base-irony` — returns `is_sarcastic`, irony probability, and severity level |
| 🔍 **LIME Explainability** | Token-level highlight map and bar chart showing which words drove the prediction; `num_samples=100` for ~10× speedup; results cached for 1 hour |
| 🌐 **Translation Pipeline** | Primary: Helsinki-NLP `opus-mt-mul-en` (offline-capable MarianMT); fallback: googletrans |
| 🤖 **AI Summary** | LSA extractive summariser (sumy) auto-generates key takeaways from negative review batches |
| 📄 **PDF Export** | One-click professional report generation with fpdf2 for single and bulk analyses |

### 🔹 UX Features

- **Glassmorphism dark UI** — custom CSS card components, deep `#070b14` background
- **Anti-flicker session state** — Streamlit `st.session_state` ensures results survive rerenders
- **Animated progress bar** — real-time pipeline progress with descriptive status messages
- **Polarity gauge** — interactive Plotly gauge chart visualising sentiment on a −1 → +1 scale
- **Multi-format export** — download results as CSV, JSON, PDF, or Excel

---

## 🛠️ Tech Stack

### Frontend
| Library | Role |
|---|---|
| **Streamlit ≥1.36** | Multi-page web app framework |
| **Custom CSS** | Glassmorphism dark theme, metric cards, tag pills |
| **Plotly ≥5.22** | Interactive charts, gauges, heatmaps |
| **Matplotlib / Seaborn** | Static figures saved to `reports/` |

### Backend & ML / NLP
| Library | Role |
|---|---|
| **Transformers ≥4.44 (HuggingFace)** | RoBERTa sentiment + irony + MarianMT translation |
| **PyTorch ≥2.3** | Tensor inference backend |
| **scikit-learn ≥1.5** | TF-IDF vectoriser, LinearSVC, Logistic Regression, Naive Bayes, Random Forest |
| **XGBoost ≥2.1** | Gradient-boosted classifier (available in training pipeline) |
| **spaCy ≥3.7** | Aspect noun-phrase extraction |
| **LIME ≥0.2** | Local Interpretable Model-Agnostic Explanations |
| **NLTK ≥3.9 / TextBlob ≥0.19** | Text preprocessing, subjectivity scoring |
| **sumy ≥0.11** | Extractive LSA summarisation |
| **langdetect ≥1.0.9** | Language identification |
| **googletrans 4.0.0-rc1** | Translation fallback |
| **sentencepiece ≥0.2** | Tokenisation for MarianMT |

### Utilities
| Library | Role |
|---|---|
| **pandas ≥2.3 / NumPy ≥2.3** | Data handling |
| **joblib ≥1.4** | Model serialisation / deserialisation |
| **fpdf2 ≥2.7** | PDF report generation |
| **openpyxl ≥3.1** | Excel export |
| **tqdm ≥4.67** | Progress bars during training |

### HuggingFace Models Used
| Model | Purpose |
|---|---|
| `cardiffnlp/twitter-roberta-base-sentiment-latest` | Core sentiment classifier (Neg / Neu / Pos) |
| `cardiffnlp/twitter-roberta-base-irony` | Sarcasm / irony detection |
| `Helsinki-NLP/opus-mt-mul-en` | Multilingual → English translation (MarianMT) |

---

## 📁 Project Structure

```
ReviewSense-Analytics/
├── app/
│   ├── app.py                      # Home page — KPI cards, capability overview, quick-actions
│   ├── utils.py                    # load_css() and load_model() shared helpers
│   └── pages/
│       ├── 01_Live_Prediction.py   # Single review analysis with LIME, ABSA, sarcasm
│       ├── 02_Bulk_Analysis.py     # CSV/Excel batch pipeline with charts and export
│       ├── 03_Model_Dashboard.py   # Classical ML comparison, confusion matrices, ROC
│       └── 04_Language_Analysis.py # Multilingual detection + translation + analysis
│
├── src/
│   ├── config.py                   # Project-wide constants (paths, model IDs, label maps, domains)
│   ├── preprocess.py               # Data cleaning, stratified train/val/test splitting
│   ├── train_classical.py          # TF-IDF + classical model training; writes reports/model_results.json
│   ├── evaluate.py                 # Metrics: accuracy, F1, confusion matrix, ROC-AUC
│   ├── predict.py                  # Classical model inference helpers
│   ├── absa.py                     # ABSA wrapper → delegates to src/models/aspect.py
│   ├── lime_explainer.py           # LIME wrapper with caching and token highlighting
│   ├── summarizer.py               # LSA extractive review summarisation
│   ├── sarcasm_detector.py         # Legacy sarcasm module (see src/models/sarcasm_model.py)
│   ├── translator.py               # Language detection & Helsinki-NLP / googletrans translation
│   ├── pdf_exporter.py             # fpdf2 PDF report generation
│   └── models/
│       ├── sentiment.py            # RoBERTa sentiment predict() / predict_batch()
│       ├── sarcasm_model.py        # RoBERTa irony predict() / predict_batch()
│       ├── translation.py          # MarianMT translation with googletrans fallback
│       ├── language.py             # langdetect wrapper with flag emoji mapping
│       └── aspect.py               # spaCy + RoBERTa ABSA
│
├── src/pipeline/
│   └── inference.py                # run_pipeline() / run_pipeline_batch() — unified NLP orchestrator
│
├── ui/
│   ├── sidebar.py                  # Shared sidebar with navigation links and CSS loader
│   ├── theme.py                    # Plotly dark theme (apply_theme()), colour palette constants
│   └── components.py               # Reusable UI components
│
├── data/
│   ├── processed/                  # reviewsense_dataset.csv (gitignored — place here manually)
│   └── exports/                    # Generated export files
│
├── models/
│   ├── classical/                  # Saved sklearn models (.pkl) + TF-IDF vectoriser
│   └── roberta/                    # Fine-tuned RoBERTa checkpoints
│
├── reports/
│   ├── model_results.json          # Training metrics (accuracy, F1, confusion_matrix, ROC, training_time_sec)
│   └── figures/                    # Saved plot images
│
├── notebooks/                      # Exploratory Jupyter notebooks
├── colab/                          # Google Colab training notebooks
├── scripts/
│   ├── generate_demo_artifacts.py  # Creates dummy model files for running the app without training
│   ├── optimize_and_train.py       # Hyperparameter optimisation script
│   ├── train_final.py              # Final production model training
│   └── verify_model.py             # Post-training model verification
│
├── requirements.txt
└── README.md
```

---

## ⚙️ How It Works — NLP Pipeline

### Single Review Pipeline (`run_pipeline`)

```
User Input (any language)
        │
        ▼
  1. Language Detection        langdetect → ISO code + flag emoji
        │
        ▼
  2. Translation (if needed)   Helsinki-NLP MarianMT → English
        │  (falls back to googletrans if MarianMT fails)
        ▼
  3. Sentiment Prediction      cardiffnlp/twitter-roberta-base-sentiment-latest
        │  → label (Neg/Neu/Pos), confidence, scores [neg, neu, pos]
        │  → polarity = scores[2] - scores[0]
        │  → subjectivity = 1.0 - scores[1]
        │  → if confidence < 0.60: label = "Uncertain"
        ▼
  4. Sarcasm Detection (opt.)  cardiffnlp/twitter-roberta-base-irony
        │  → is_sarcastic, irony_probability, severity
        ▼
  5. Aspect Analysis (opt.)    spaCy noun-phrase extraction + RoBERTa polarity per aspect
        ▼
  6. LIME Explanation (opt.)   LimeTextExplainer (num_samples=100) → word weights + HTML highlight
        │
        ▼
  Output dict: sentiment, confidence, polarity, subjectivity,
               sarcasm, aspects, language, translated text
```

### Batch Pipeline (`run_pipeline_batch`)

```
CSV / Excel upload
        │
        ▼
  Per-row: Language detect + translate    (unavoidable — different languages per row)
        ▼
  Vectorized sentiment (batch_size=32)    ~10× faster than per-row inference
        ▼
  Vectorized sarcasm  (batch_size=16)     optional, enabled by toggle
        ▼
  Per-row aspect analysis                 optional, enabled by toggle
        ▼
  Enriched DataFrame: +Sentiment, +Confidence, +Polarity, +Subjectivity, +Language, +Sarcasm
        ▼
  Charts: Pie distribution, top keywords, sentiment trend line
        ▼
  Export: CSV / JSON / PDF / Excel
```

### Multilingual Pipeline

```
Non-English Text
     │
     ▼  langdetect (ISO 639-1 code)
     ▼  Helsinki-NLP/opus-mt-mul-en  ──[fail]──▶  googletrans fallback
     ▼  English translation
     ▼  Full sentiment + LIME pipeline on translated text
     ▼  Results tagged with detected language + flag emoji
```

---

## 🚀 Installation — Local Setup

### Prerequisites

- Python 3.10+
- pip
- (Optional) GPU with CUDA for faster transformer inference

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/amansethhh/ReviewSense-Analytics.git
cd ReviewSense-Analytics

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download the spaCy language model (required for Aspect-Based Sentiment Analysis)
python -m spacy download en_core_web_sm

# 4a. Quick demo (no dataset required)
#     Generates placeholder model artifacts so the dashboard runs immediately
python scripts/generate_demo_artifacts.py

# 4b. OR: Train on the full dataset
#     Copy reviewsense_dataset.csv → data/processed/reviewsense_dataset.csv
python src/preprocess.py
python src/train_classical.py

# 5. Launch the Streamlit dashboard
streamlit run app/app.py
```

The app will open at `http://localhost:8501`.

> **Note:** On first run the transformer models (`cardiffnlp/twitter-roberta-base-sentiment-latest`, `cardiffnlp/twitter-roberta-base-irony`, `Helsinki-NLP/opus-mt-mul-en`) will be downloaded from HuggingFace Hub (~1–2 GB total). They are then cached locally and loaded in seconds on subsequent runs.

---

## ☁️ Deployment — Streamlit Cloud

1. Push your repository to GitHub (models and large data files must be gitignored or use Git LFS).
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Click **New app**, select your repository and set the main file path to `app/app.py`.
4. Add any required secrets (e.g., API keys) in the **Secrets** panel if needed.
5. Click **Deploy**. Streamlit Cloud will install `requirements.txt` automatically.

> **Tip:** Transformer models will be re-downloaded on each cold start in Streamlit Cloud. If startup time matters, pin model downloads to a persistent cache volume or use `@st.cache_resource` with a custom cache directory.

---

## ⚡ Performance Optimizations

| Technique | Where | Effect |
|---|---|---|
| `@st.cache_resource` | `sentiment.py`, `sarcasm_model.py`, `translation.py` | Transformer models loaded **once** per session — instant on subsequent calls |
| `@st.cache_data(ttl=3600)` | `lime_explainer.py → explain_prediction()` | LIME results cached for 1 hour — repeat analyses are instant |
| `LIME_NUM_SAMPLES = 100` | `lime_explainer.py` | ~10× speedup vs. default 5000 samples |
| Chunked batch inference (`batch_size=32`) | `sentiment.py → predict_batch()` | Vectorized inference prevents OOM on large datasets |
| Chunked batch sarcasm (`batch_size=16`) | `sarcasm_model.py → predict_batch()` | Sarcasm on thousands of rows without memory spikes |
| `st.session_state` for results | All page files | Results survive Streamlit rerenders — no redundant model calls |
| Real-time progress callback | `inference.py → run_pipeline_batch()` | UI stays responsive with `progress_callback(pct, msg)` during long batches |
| `preload_models()` | `inference.py` | Eager model initialization at page load eliminates cold-start latency |

---

## 📝 Sample Inputs

| Review | Expected Sentiment |
|---|---|
| `"The battery lasts all day and the camera quality is exceptional."` | ✅ Positive |
| `"Delivery took 3 weeks, product was damaged, never buying again."` | ❌ Negative |
| `"It works as described. Nothing special, nothing bad."` | ◼ Neutral |
| `"Oh great, another product that breaks after two uses. Fantastic."` | 😏 Sarcasm + Negative |
| `"La batterie dure longtemps, mais l'écran est trop sombre."` | 🌐 French → Negative (screen too dark) |
| `"बहुत अच्छा उत्पाद है, मुझे बहुत पसंद आया।"` | 🌐 Hindi → Positive |

---

## 📊 Output Explanation

| Field | Description |
|---|---|
| **Sentiment** | `Positive` / `Negative` / `Neutral` / `Uncertain` (when confidence < 60%) |
| **Confidence** | Softmax probability of the top class (0–100%) |
| **Polarity** | `scores[Positive] − scores[Negative]` (range −1 to +1) |
| **Subjectivity** | `1.0 − scores[Neutral]` — higher means more opinionated text |
| **LIME bar chart** | Top 6 words and their contribution weight toward the predicted class |
| **ABSA table** | Detected aspects (nouns/noun-phrases) with individual polarity scores |
| **Sarcasm badge** | `⚠️ SARCASM DETECTED` with irony probability, or `✅ NO SARCASM` |
| **Polarity gauge** | Plotly gauge from −1 (very negative) to +1 (very positive) |

---

## ⚠️ Limitations

- **Sarcasm accuracy** — The Cardiff RoBERTa irony model is trained on Twitter data; performance may degrade on formal or domain-specific text.
- **Neutral class recall** — Classical ML models show low recall for the Neutral class (Macro F1 on neutral: 0.01–0.13) due to class imbalance; SMOTE or class-weighted training is recommended.
- **LIME latency** — First-run LIME generation takes a few seconds (100 perturbation samples × RoBERTa inference). Results are then cached for 1 hour.
- **Translation edge cases** — Helsinki-NLP MarianMT is a general multi-to-English model; domain-specific terminology (e.g., technical jargon, brand names) may not translate accurately.
- **Dataset size** — The full `reviewsense_dataset.csv` (~1.3 M rows) is not included due to file-size constraints; classical models need this to be retrained locally.
- **Uncertainty threshold** — Reviews with confidence < 60% are labelled `Uncertain`; this threshold is fixed and not currently configurable from the UI.

---

## 🔭 Future Improvements

- [ ] **Real-time REST API** — FastAPI wrapper around `run_pipeline()` for programmatic access
- [ ] **Fine-tune RoBERTa on domain data** — Custom training on reviewsense_dataset for higher domain accuracy
- [ ] **SMOTE / class-weighted training** — Address the Neutral-class imbalance in classical models
- [ ] **Async LIME** — Run LIME in a background thread to return sentiment results immediately
- [ ] **Cloud scaling** — Containerise with Docker and deploy on GCP / AWS / Azure
- [ ] **User-configurable confidence threshold** — UI slider for the "Uncertain" label cutoff
- [ ] **More export formats** — PowerPoint, HTML reports
- [ ] **Dashboard authentication** — Add login layer for enterprise deployment

---

## 👤 Author

**Aman Seth**  
AI Developer · NLP Engineer

---

## 📄 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

