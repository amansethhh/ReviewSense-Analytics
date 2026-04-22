"""Debug: check RoBERTa vs XLM-R for German/French edge cases."""
import sys
sys.stdout.reconfigure(encoding='utf-8', errors='replace')

from src.models.sentiment import predict
from src.models.language import detect_language

cases = [
    ("Sehr schlecht, ich bin entt\u00e4uscht", "de"),
    ("C'est moyen, rien de sp\u00e9cial", "fr"),
    ("Das ist fantastisch, sehr gute Qualit\u00e4t", "de"),
    ("Arrived on time, standard packaging", "en"),
]

for text, expected_lang in cases:
    lang = detect_language(text)
    roberta = predict(text, lang_code="en")
    xlmr = predict(text, lang_code=expected_lang)
    print(f"Text: {text}")
    print(f"  Detected lang: {lang['code']}")
    print(f"  RoBERTa: {roberta['label_name']:8s} conf={roberta['confidence']:.3f}")
    print(f"  XLM-R:   {xlmr['label_name']:8s} conf={xlmr['confidence']:.3f}")
    print()
