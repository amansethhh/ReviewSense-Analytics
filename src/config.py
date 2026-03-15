# src/config.py
# Project-wide constants for ReviewSense Analytics

RAW_DATA_PATH = "data/processed/reviewsense_dataset.csv"
PROCESSED_DIR = "data/processed/"
MODELS_DIR = "models/classical/"
ROBERTA_DIR = "models/roberta/reviewsense_roberta/"
REPORTS_DIR = "reports/"

LABEL_MAP = {0: "Negative", 1: "Neutral", 2: "Positive"}
LABEL_COLORS = {0: "#ff4b4b", 1: "#ffa500", 2: "#00c851"}

DOMAINS = ["food_product", "movie", "airline", "ecommerce_india", "social_media"]
MODEL_NAMES = ["Naive Bayes", "LinearSVC", "Logistic Regression", "Random Forest"]

MAX_FEATURES = 15000
NGRAM_RANGE = (1, 2)
TEST_SIZE = 0.2
VAL_SIZE = 0.1
RANDOM_STATE = 42
SAMPLE_SIZE = 300000  # rows to use for training (memory-safe)
