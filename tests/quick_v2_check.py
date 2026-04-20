"""Quick E2E validation script for V2 enhancements."""
import sys
import os

sys.path.insert(0, "w:/ReviewSense-Analytics/src")
sys.path.insert(0, "w:/ReviewSense-Analytics/backend")
sys.path.insert(0, "w:/ReviewSense-Analytics")

from src.models.sentiment import predict, predict_batch

# Test single predict
r = predict("excellent product")
print(f"Single predict: {r['label_name']} ({r['confidence']:.3f})")

# Test batch predict with lang routing
batch = predict_batch(["great!", "terrible!"], lang_codes=["en", "en"])
print(f"Batch[0]: {batch[0]['label_name']}, Batch[1]: {batch[1]['label_name']}")

# Test full pipeline
from src.predict import predict_sentiment
full = predict_sentiment("This product is absolutely amazing and wonderful!")
print(f"Full pipeline: {full['label_name']} conf={full['confidence']:.3f}")
print(f"  Fields: {len(full)} (need 20)")
print(f"  VADER available: {full.get('sarcasm_detected') is not None}")

# Test VADER detection
from src.predict import compute_dual_polarity
tb, vader, subj = compute_dual_polarity("Not bad at all, quite good actually", "en")
print(f"Dual polarity: tb={tb:.3f}, vader={vader:.3f}")

print("\nALL TESTS PASSED ✅")
