"""
ReviewSense V5 — Global System Architecture Definition.

Single source of truth for the production pipeline vs. benchmark model
separation. Every UI, API, and export layer should reference this
constant to avoid inconsistency.
"""

SYSTEM_INFO = {
    "production_pipeline": {
        "name": "Hybrid Transformer Pipeline",
        "version": "V5",
        "accuracy": "95.8%",
        "models": ["RoBERTa", "XLM-R"],
        "translation": "NLLB (facebook/nllb-200-distilled-600M)",
        "routing": {
            "english": "RoBERTa",
            "hinglish": "RoBERTa (after normalization)",
            "multilingual": "XLM-R (with NLLB translation trust gate)",
        },
        "decision_layer": "Entropy + Margin based confidence thresholding",
        "description": (
            "Dynamic routing with Hinglish normalization, "
            "translation trust validation, and entropy-based "
            "decision layer. 95.8% verified accuracy."
        ),
    },
    "benchmark_models": [
        {
            "name": "LinearSVC",
            "type": "Classical ML",
            "note": "Best benchmark model by Macro F1 — offline evaluation only",
        },
        {
            "name": "Logistic Regression",
            "type": "Classical ML",
            "note": "Fastest classical model — offline evaluation only",
        },
        {
            "name": "Naive Bayes",
            "type": "Classical ML",
            "note": "Probabilistic baseline — offline evaluation only",
        },
        {
            "name": "Random Forest",
            "type": "Classical ML",
            "note": "Ensemble baseline — offline evaluation only",
        },
    ],
    "benchmark_disclaimer": (
        "These models are used for offline evaluation only "
        "and are NOT part of the live prediction system. "
        "Production inference uses the Hybrid Transformer Pipeline."
    ),
}
