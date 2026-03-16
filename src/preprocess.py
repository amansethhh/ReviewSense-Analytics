"""Preprocessing pipeline for ReviewSense Analytics."""

from __future__ import annotations

import html
import re
import warnings
from functools import lru_cache
from pathlib import Path
from typing import Optional

import nltk
import numpy as np
import pandas as pd
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import wordpunct_tokenize
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
from sklearn.model_selection import train_test_split

from src.config import PROCESSED_DIR, RAW_DATA_PATH


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_FILE = PROJECT_ROOT / RAW_DATA_PATH
PROCESSED_PATH = PROJECT_ROOT / PROCESSED_DIR


TEXT_KEYWORDS = ("text", "review", "sentence", "content", "tweet")
LABEL_KEYWORDS = ("label", "sentiment", "rating", "score", "polarity")


HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
MENTION_PATTERN = re.compile(r"@\w+")
HASHTAG_PATTERN = re.compile(r"#\w+")
NON_ASCII_PATTERN = re.compile(r"[^\x00-\x7F]+")
WHITESPACE_PATTERN = re.compile(r"\s+")
PUNCT_PATTERN = re.compile(r"[^a-z0-9\s]+")


class _FallbackLemmatizer:
    def lemmatize(self, token: str) -> str:
        return token


# ----------------------------------------------------
# Stopwords + Lemmatizer
# ----------------------------------------------------

@lru_cache(maxsize=1)
def _get_stop_words():

    try:
        return set(stopwords.words("english"))

    except LookupError:

        try:
            nltk.download("stopwords", quiet=True)
            return set(stopwords.words("english"))

        except Exception:

            warnings.warn("Using sklearn stopwords")

            return set(ENGLISH_STOP_WORDS)


@lru_cache(maxsize=1)
def _get_lemmatizer():

    lemmatizer = WordNetLemmatizer()

    try:
        lemmatizer.lemmatize("cars")
        return lemmatizer

    except LookupError:

        try:
            nltk.download("wordnet", quiet=True)
            nltk.download("omw-1.4", quiet=True)
            return lemmatizer

        except Exception:

            warnings.warn("WordNet unavailable")

            return _FallbackLemmatizer()


# ----------------------------------------------------
# Column Detection
# ----------------------------------------------------

def detect_columns(df: pd.DataFrame):

    text_col = None
    label_col = None

    for col in df.columns:

        name = col.lower()

        if any(k in name for k in TEXT_KEYWORDS):
            text_col = col

        if any(k in name for k in LABEL_KEYWORDS):
            label_col = col

    if text_col is None or label_col is None:

        raise ValueError(
            f"Could not detect text/label columns.\nColumns found: {list(df.columns)}"
        )

    return text_col, label_col


# ----------------------------------------------------
# Label Conversion
# ----------------------------------------------------

def normalize_label(val) -> Optional[int]:
    """Convert heterogeneous labels safely to 0/1/2."""

    if val is None or pd.isna(val):
        return None

    # Already valid labels
    if val in {0, 1, 2}:
        return int(val)

    # numeric ratings
    if isinstance(val, (int, float, np.integer, np.floating)):

        rating = float(val)

        # rating scale 1–5
        if rating <= 2:
            return 0
        elif rating == 3:
            return 1
        elif rating >= 4:
            return 2

    # text labels
    if isinstance(val, str):

        val = val.strip().lower()

        mapping = {
            "positive": 2,
            "pos": 2,
            "negative": 0,
            "neg": 0,
            "neutral": 1,
            "neu": 1,
        }

        if val in mapping:
            return mapping[val]

        try:
            return normalize_label(float(val))
        except:
            return None

    return None

# ----------------------------------------------------
# Text Cleaning
# ----------------------------------------------------

def clean_text(text: str):

    if text is None or pd.isna(text):
        return None

    text = html.unescape(str(text))

    text = HTML_TAG_PATTERN.sub(" ", text)
    text = URL_PATTERN.sub(" ", text)
    text = MENTION_PATTERN.sub(" ", text)
    text = HASHTAG_PATTERN.sub(" ", text)

    text = NON_ASCII_PATTERN.sub(" ", text)

    text = text.lower()

    text = PUNCT_PATTERN.sub(" ", text)

    text = WHITESPACE_PATTERN.sub(" ", text).strip()

    if len(text) < 15:
        return None

    return text


# ----------------------------------------------------
# NLP Preprocessing
# ----------------------------------------------------

def preprocess_pipeline(text):

    cleaned = clean_text(text)

    if cleaned is None:
        return None

    stop_words = _get_stop_words()

    lemmatizer = _get_lemmatizer()

    tokens = [

        t

        for t in wordpunct_tokenize(cleaned)

        if t.isalpha() and t not in stop_words and len(t) > 2

    ]

    if not tokens:
        return None

    tokens = [lemmatizer.lemmatize(t) for t in tokens]

    processed = " ".join(tokens)

    if len(processed) < 10:
        return None

    return processed


# ----------------------------------------------------
# Load Dataset
# ----------------------------------------------------

def load_and_prepare(sample_size=300000, random_state=42):

    if not RAW_DATA_FILE.exists():

        raise FileNotFoundError(f"Dataset not found: {RAW_DATA_FILE}")

    preview = pd.read_csv(RAW_DATA_FILE, nrows=2000)

    text_col, label_col = detect_columns(preview)

    print("Detected columns:", {"text": text_col, "label": label_col})

    df = pd.read_csv(RAW_DATA_FILE, usecols=[text_col, label_col])

    df = df.rename(columns={text_col: "text", label_col: "label"})

    df = df.dropna(subset=["text", "label"])

    df["label"] = df["label"].apply(normalize_label)

    df["text"] = df["text"].apply(preprocess_pipeline)

    df = df.dropna(subset=["text", "label"])

    df["label"] = df["label"].astype(int)

    df = df.sample(frac=1, random_state=random_state)

    if len(df) > sample_size:

        df, _ = train_test_split(

            df,

            train_size=sample_size,

            stratify=df["label"],

            random_state=random_state,

        )

    print(f"Prepared rows: {len(df):,}")

    print("Label distribution:")

    print(df["label"].value_counts(normalize=True).round(4))

    return df


# ----------------------------------------------------
# Train / Val / Test Split
# ----------------------------------------------------

def split_and_save():

    PROCESSED_PATH.mkdir(parents=True, exist_ok=True)

    df = load_and_prepare()

    unified_clean_path = PROCESSED_PATH / "unified_clean.csv"

    df.to_csv(unified_clean_path, index=False)

    train, temp = train_test_split(

        df,

        test_size=0.2,

        stratify=df["label"],

        random_state=42,

    )

    val, test = train_test_split(

        temp,

        test_size=0.5,

        stratify=temp["label"],

        random_state=42,

    )

    np.save(PROCESSED_PATH / "X_train.npy", train["text"].values)

    np.save(PROCESSED_PATH / "X_val.npy", val["text"].values)

    np.save(PROCESSED_PATH / "X_test.npy", test["text"].values)

    np.save(PROCESSED_PATH / "y_train.npy", train["label"].values)

    np.save(PROCESSED_PATH / "y_val.npy", val["label"].values)

    np.save(PROCESSED_PATH / "y_test.npy", test["label"].values)

    print(f"Unified dataset saved to: {unified_clean_path}")

    print(f"Train: {train.shape}")

    print(f"Validation: {val.shape}")

    print(f"Test: {test.shape}")


if __name__ == "__main__":

    split_and_save()