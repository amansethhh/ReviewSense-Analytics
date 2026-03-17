# src/config.py
# Project-wide constants for ReviewSense Analytics

from pathlib import Path

# =========================
# Paths
# =========================

PROJECT_ROOT = Path(__file__).resolve().parents[1]

RAW_DATA_PATH = "data/processed/reviewsense_dataset.csv"
PROCESSED_DIR = "data/processed/"
MODELS_DIR = "models/classical/"
ROBERTA_DIR = "models/roberta/reviewsense_roberta/"
REPORTS_DIR = "reports/"

# =========================
# HuggingFace Model IDs
# =========================

HF_SENTIMENT_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"
HF_SARCASM_MODEL = "cardiffnlp/twitter-roberta-base-irony"
HF_TRANSLATION_MODEL = "Helsinki-NLP/opus-mt-mul-en"

# =========================
# Label Mapping
# =========================
# Matches RoBERTa sentiment model output:
# 0=negative, 1=neutral, 2=positive

LABEL_MAP = {
    0: "Negative",
    1: "Neutral",
    2: "Positive",
}

# Reverse lookup (used by UI or evaluation tools)
LABEL_TO_INT = {v: k for k, v in LABEL_MAP.items()}

# Colors for dashboard display
LABEL_COLORS = {
    0: "#ff4b4b",  # red
    1: "#ffa500",  # orange
    2: "#00c851",  # green
}

# =========================
# Domains used in UI filters
# =========================

DOMAINS = [
    "food_product",
    "movie",
    "airline",
    "ecommerce_india",
    "social_media",
]

# =========================
# Available Models (UI display names)
# =========================

MODEL_NAMES = [
    "RoBERTa (Transformer)",
]

# =========================
# Training Configuration (kept for classical model compat)
# =========================

MAX_FEATURES = 15000
NGRAM_RANGE = (1, 2)

TEST_SIZE = 0.2
VAL_SIZE = 0.1

RANDOM_STATE = 42

# Maximum rows used during preprocessing
SAMPLE_SIZE = 300000