"""
src/train_classical.py
----------------------
Training pipeline for classical ML models (Naive Bayes, LinearSVC,
Logistic Regression, Random Forest) using TF-IDF features.

Responsibilities:
- Build TF-IDF vectoriser with MAX_FEATURES and NGRAM_RANGE from config
- Train each model defined in MODEL_NAMES
- Perform cross-validation and hyperparameter search
- Persist trained models and vectoriser to MODELS_DIR
"""
