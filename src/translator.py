"""
src/translator.py
-----------------
Multilingual translation and language detection module.

Responsibilities:
- Detect the language of incoming review text using langdetect
- Translate non-English reviews to English via googletrans
- Cache translations to avoid redundant API calls
"""
