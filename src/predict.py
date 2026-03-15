"""
src/predict.py
--------------
Inference helpers for ReviewSense Analytics.

Responsibilities:
- Load the best trained model and TF-IDF vectoriser
- Expose a predict(text) function that returns label and confidence
- Support batch prediction for bulk CSV uploads
- Integrate domain detection for domain-aware predictions
"""
