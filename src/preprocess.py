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

TEXT_KEYWORDS = ("text", "review", "sentence", "content", "tweet")
LABEL_KEYWORDS = ("label", "sentiment", "rating", "score", "polarity")
DOMAIN_KEYWORDS = ("domain", "source", "category", "origin", "dataset", "vertical")
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DATA_FILE = PROJECT_ROOT / RAW_DATA_PATH
PROCESSED_PATH = PROJECT_ROOT / PROCESSED_DIR

HTML_TAG_PATTERN = re.compile(r"<[^>]+>")
URL_PATTERN = re.compile(r"https?://\S+|www\.\S+", re.IGNORECASE)
MENTION_PATTERN = re.compile(r"@\w+")
HASHTAG_PATTERN = re.compile(r"#\w+")
NON_ASCII_PATTERN = re.compile(r"[^\x00-\x7F]+")
WHITESPACE_PATTERN = re.compile(r"\s+")
NON_ALPHA_PATTERN = re.compile(r"[^a-z0-9]+")


class _FallbackLemmatizer:
    """Safe fallback when WordNet data is unavailable."""

    def lemmatize(self, token: str) -> str:
        return token


def _normalize_column_name(column_name: str) -> str:
    return NON_ALPHA_PATTERN.sub(" ", str(column_name).strip().lower()).strip()


def _keyword_score(column_name: str, keywords: tuple[str, ...]) -> int:
    normalized_name = _normalize_column_name(column_name)
    tokens = set(normalized_name.split())
    score = 0

    for keyword in keywords:
        if normalized_name == keyword:
            score += 10
        if keyword in tokens:
            score += 6
        elif normalized_name.startswith(f"{keyword} ") or normalized_name.endswith(f" {keyword}"):
            score += 4
        elif keyword in normalized_name:
            score += 2

    return score


def _series_preview(series: pd.Series, sample_size: int = 500) -> pd.Series:
    return series.dropna().head(sample_size)


def _text_column_score(df: pd.DataFrame, column_name: str) -> tuple[int, float]:
    series = df[column_name]
    preview = _series_preview(series, sample_size=300)
    score = _keyword_score(column_name, TEXT_KEYWORDS)

    if score <= 0:
        return 0, 0.0

    if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
        score += 3
    elif pd.api.types.is_numeric_dtype(series):
        score -= 4

    if not preview.empty:
        preview_as_text = preview.astype(str)
        average_length = float(preview_as_text.str.len().mean())
        unique_ratio = float(preview_as_text.nunique() / max(len(preview_as_text), 1))

        if average_length >= 40:
            score += 4
        elif average_length >= 15:
            score += 2

        if unique_ratio >= 0.7:
            score += 2
    else:
        average_length = 0.0

    return score, average_length


def _label_column_score(df: pd.DataFrame, column_name: str) -> tuple[int, float]:
    series = df[column_name]
    preview = _series_preview(series, sample_size=500)
    score = _keyword_score(column_name, LABEL_KEYWORDS)

    if score <= 0:
        return 0, 0.0

    if preview.empty:
        return score, 0.0

    normalized_preview = preview.map(normalize_label)
    recognized_ratio = float(normalized_preview.notna().mean())
    unique_count = float(preview.nunique(dropna=True))

    if pd.api.types.is_numeric_dtype(series):
        score += 2
    if unique_count <= 10:
        score += 2
    score += int(recognized_ratio * 10)

    return score, recognized_ratio


def _domain_column_score(df: pd.DataFrame, column_name: str) -> tuple[int, int]:
    series = df[column_name]
    preview = _series_preview(series, sample_size=500)
    score = _keyword_score(column_name, DOMAIN_KEYWORDS)

    if score <= 0:
        return 0, 0

    if pd.api.types.is_object_dtype(series) or pd.api.types.is_string_dtype(series):
        score += 2
    elif pd.api.types.is_numeric_dtype(series):
        score -= 3

    unique_count = int(preview.astype(str).nunique()) if not preview.empty else 0
    if 2 <= unique_count <= 100:
        score += 3

    return score, unique_count


@lru_cache(maxsize=1)
def _get_stop_words() -> set[str]:
    try:
        return set(stopwords.words("english"))
    except LookupError:
        try:
            nltk.download("stopwords", quiet=True)
            return set(stopwords.words("english"))
        except Exception:
            warnings.warn(
                "NLTK stopwords corpus is unavailable; falling back to sklearn stop words.",
                stacklevel=2,
            )
            return set(ENGLISH_STOP_WORDS)


@lru_cache(maxsize=1)
def _get_lemmatizer() -> WordNetLemmatizer | _FallbackLemmatizer:
    lemmatizer = WordNetLemmatizer()

    try:
        lemmatizer.lemmatize("cars")
        return lemmatizer
    except LookupError:
        try:
            nltk.download("wordnet", quiet=True)
            nltk.download("omw-1.4", quiet=True)
            lemmatizer.lemmatize("cars")
            return lemmatizer
        except Exception:
            warnings.warn(
                "NLTK WordNet data is unavailable; using identity lemmatization.",
                stacklevel=2,
            )
            return _FallbackLemmatizer()


def _detect_optional_domain_column(df: pd.DataFrame, excluded_columns: set[str]) -> Optional[str]:
    candidates: list[tuple[int, int, str]] = []

    for column_name in df.columns:
        if column_name in excluded_columns:
            continue

        score, unique_count = _domain_column_score(df, column_name)
        if score > 0:
            candidates.append((score, unique_count, column_name))

    if not candidates:
        return None

    candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    return candidates[0][2]


def _stratify_target(values: pd.Series) -> Optional[pd.Series]:
    class_counts = values.value_counts(dropna=False)
    if class_counts.empty or class_counts.min() < 2 or values.nunique() < 2:
        return None
    return values


def _sample_stratified(df: pd.DataFrame, sample_size: int, random_state: int) -> pd.DataFrame:
    if sample_size is None or sample_size <= 0 or len(df) <= sample_size:
        return df

    stratify_values = _stratify_target(df["label"])

    try:
        sampled_df, _ = train_test_split(
            df,
            train_size=sample_size,
            random_state=random_state,
            stratify=stratify_values,
        )
        return sampled_df.reset_index(drop=True)
    except ValueError as exc:
        warnings.warn(
            f"Stratified sampling failed ({exc}); falling back to random sampling.",
            stacklevel=2,
        )
        return df.sample(n=sample_size, random_state=random_state).reset_index(drop=True)


def _train_test_split_stratified(
    df: pd.DataFrame,
    test_size: float,
    random_state: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    stratify_values = _stratify_target(df["label"])

    try:
        first, second = train_test_split(
            df,
            test_size=test_size,
            random_state=random_state,
            stratify=stratify_values,
        )
        return first.reset_index(drop=True), second.reset_index(drop=True)
    except ValueError as exc:
        warnings.warn(
            f"Stratified split failed ({exc}); falling back to random split.",
            stacklevel=2,
        )
        first, second = train_test_split(
            df,
            test_size=test_size,
            random_state=random_state,
            stratify=None,
        )
        return first.reset_index(drop=True), second.reset_index(drop=True)


def detect_columns(df: pd.DataFrame) -> tuple[str, str]:
    """Auto-detect text and label columns from any column name variant."""

    if df.empty:
        raise ValueError("Cannot detect columns from an empty DataFrame.")

    text_candidates: list[tuple[int, float, str]] = []
    label_candidates: list[tuple[int, float, str]] = []

    for column_name in df.columns:
        text_score, average_length = _text_column_score(df, column_name)
        if text_score > 0:
            text_candidates.append((text_score, average_length, column_name))

        label_score, recognized_ratio = _label_column_score(df, column_name)
        if label_score > 0:
            label_candidates.append((label_score, recognized_ratio, column_name))

    if not text_candidates:
        available_columns = ", ".join(map(str, df.columns))
        raise ValueError(
            "Unable to detect the text column. Expected a column name containing one of "
            f"{TEXT_KEYWORDS}. Available columns: {available_columns}"
        )

    if not label_candidates:
        available_columns = ", ".join(map(str, df.columns))
        raise ValueError(
            "Unable to detect the label column. Expected a column name containing one of "
            f"{LABEL_KEYWORDS}. Available columns: {available_columns}"
        )

    text_candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
    label_candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)

    text_col_name = text_candidates[0][2]
    label_col_name = label_candidates[0][2]

    if text_col_name == label_col_name:
        alternative_labels = [candidate[2] for candidate in label_candidates if candidate[2] != text_col_name]
        if not alternative_labels:
            raise ValueError(
                "Detected the same column for text and label. Please inspect the dataset schema manually."
            )
        label_col_name = alternative_labels[0]

    return text_col_name, label_col_name


def clean_text(text: str) -> Optional[str]:
    """Normalize raw text and remove unusable rows."""

    if text is None or pd.isna(text):
        return None

    normalized_text = html.unescape(str(text))
    normalized_text = HTML_TAG_PATTERN.sub(" ", normalized_text)
    normalized_text = URL_PATTERN.sub(" ", normalized_text)
    normalized_text = MENTION_PATTERN.sub(" ", normalized_text)
    normalized_text = HASHTAG_PATTERN.sub(" ", normalized_text)
    normalized_text = NON_ASCII_PATTERN.sub(" ", normalized_text)
    normalized_text = normalized_text.lower()
    normalized_text = WHITESPACE_PATTERN.sub(" ", normalized_text).strip()

    if len(normalized_text) < 10:
        return None

    return normalized_text


def normalize_label(val) -> Optional[int]:
    """Convert heterogeneous label formats into 0/1/2."""

    if val is None or pd.isna(val):
        return None

    if isinstance(val, (np.integer, int)):
        int_value = int(val)
        if int_value in {0, 1, 2}:
            return int_value
        if int_value >= 4:
            return 2
        if int_value == 3:
            return 1
        if int_value <= 2:
            return 0
        return None

    if isinstance(val, (np.floating, float)):
        float_value = float(val)
        if float_value.is_integer() and int(float_value) in {0, 1, 2}:
            return int(float_value)
        if float_value >= 4.0:
            return 2
        if float_value == 3.0:
            return 1
        if float_value <= 2.0:
            return 0
        return None

    if isinstance(val, str):
        cleaned_value = val.strip().lower()
        if not cleaned_value:
            return None

        normalized_value = re.sub(r"[^a-z0-9.]+", " ", cleaned_value).strip()
        label_map = {
            "positive": 2,
            "pos": 2,
            "negative": 0,
            "neg": 0,
            "neutral": 1,
            "neu": 1,
        }

        if normalized_value in label_map:
            return label_map[normalized_value]

        tokens = normalized_value.split()
        for token in tokens:
            if token in label_map:
                return label_map[token]

        try:
            numeric_value = float(normalized_value)
        except ValueError:
            return None

        return normalize_label(numeric_value)

    return None


def preprocess_pipeline(text: str) -> Optional[str]:
    """Clean, tokenize, remove stop words, lemmatize, and rejoin text."""

    cleaned_text = clean_text(text)
    if cleaned_text is None:
        return None

    stop_words = _get_stop_words()
    lemmatizer = _get_lemmatizer()

    tokens = [
        token
        for token in wordpunct_tokenize(cleaned_text)
        if token.isalpha() and token not in stop_words and len(token) > 1
    ]

    if not tokens:
        return None

    processed_text = " ".join(lemmatizer.lemmatize(token) for token in tokens).strip()
    if len(processed_text) < 10:
        return None

    return processed_text


def load_and_prepare(sample_size: int = 300000, random_state: int = 42) -> pd.DataFrame:
    """Load, normalize, clean, and sample the processed dataset."""

    if not RAW_DATA_FILE.exists():
        raise FileNotFoundError(f"Dataset not found: {RAW_DATA_FILE}")

    preview_df = pd.read_csv(
        RAW_DATA_FILE,
        nrows=2000,
        low_memory=False,
        encoding_errors="ignore",
    )
    text_col_name, label_col_name = detect_columns(preview_df)
    domain_col_name = _detect_optional_domain_column(
        preview_df,
        excluded_columns={text_col_name, label_col_name},
    )

    use_columns = [text_col_name, label_col_name]
    if domain_col_name is not None:
        use_columns.append(domain_col_name)

    print(
        "Detected columns:",
        {
            "text": text_col_name,
            "label": label_col_name,
            "domain": domain_col_name,
        },
    )

    df = pd.read_csv(
        RAW_DATA_FILE,
        usecols=use_columns,
        low_memory=False,
        encoding_errors="ignore",
    )

    rename_map = {text_col_name: "text", label_col_name: "label"}
    if domain_col_name is not None:
        rename_map[domain_col_name] = "domain"

    working_df = df.rename(columns=rename_map).copy()
    working_df = working_df.dropna(subset=["text", "label"])

    working_df["label"] = working_df["label"].map(normalize_label)
    working_df["text"] = working_df["text"].map(preprocess_pipeline)

    if "domain" in working_df.columns:
        working_df["domain"] = (
            working_df["domain"]
            .fillna("unknown")
            .astype(str)
            .str.strip()
            .replace("", "unknown")
        )

    working_df = working_df.dropna(subset=["text", "label"]).copy()
    working_df["label"] = working_df["label"].astype(int)

    output_columns = ["text", "label"]
    if "domain" in working_df.columns:
        output_columns.append("domain")

    working_df = working_df.loc[:, output_columns].reset_index(drop=True)
    working_df = _sample_stratified(working_df, sample_size=sample_size, random_state=random_state)

    print(f"Prepared rows: {len(working_df):,}")
    print("Label distribution:")
    print(working_df["label"].value_counts(normalize=True).sort_index().round(4))

    return working_df


def split_and_save() -> None:
    """Create 80/10/10 splits and persist processed artifacts to disk."""

    PROCESSED_PATH.mkdir(parents=True, exist_ok=True)

    prepared_df = load_and_prepare()
    unified_clean_path = PROCESSED_PATH / "unified_clean.csv"
    prepared_df.to_csv(unified_clean_path, index=False)

    train_df, temp_df = _train_test_split_stratified(
        prepared_df,
        test_size=0.2,
        random_state=42,
    )
    val_df, test_df = _train_test_split_stratified(
        temp_df,
        test_size=0.5,
        random_state=42,
    )

    np.save(PROCESSED_PATH / "X_train.npy", train_df["text"].to_numpy(dtype=str))
    np.save(PROCESSED_PATH / "X_val.npy", val_df["text"].to_numpy(dtype=str))
    np.save(PROCESSED_PATH / "X_test.npy", test_df["text"].to_numpy(dtype=str))
    np.save(PROCESSED_PATH / "y_train.npy", train_df["label"].to_numpy(dtype=np.int64))
    np.save(PROCESSED_PATH / "y_val.npy", val_df["label"].to_numpy(dtype=np.int64))
    np.save(PROCESSED_PATH / "y_test.npy", test_df["label"].to_numpy(dtype=np.int64))

    print(f"Unified clean dataset saved to: {unified_clean_path}")
    print(f"X_train shape: {train_df['text'].shape}, y_train shape: {train_df['label'].shape}")
    print(f"X_val shape: {val_df['text'].shape}, y_val shape: {val_df['label'].shape}")
    print(f"X_test shape: {test_df['text'].shape}, y_test shape: {test_df['label'].shape}")


if __name__ == "__main__":
    split_and_save()
