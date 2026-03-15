"""
src/preprocess.py
-----------------
Data loading and preprocessing pipeline for ReviewSense Analytics.

Responsibilities:
- Load raw CSV dataset from RAW_DATA_PATH
- Inspect and validate columns
- Clean text (lowercasing, punctuation removal, stopword removal)
- Balance classes per domain if needed
- Split into train / validation / test sets
- Persist processed splits to PROCESSED_DIR
"""
