"""
src/summarizer.py
-----------------
Extractive review summarisation module using sumy.

Responsibilities:
- Accept a list of review texts for a product / entity
- Return a concise extractive summary (top-N sentences)
- Support configurable summarisation algorithms (LSA, LexRank, Luhn)
"""

from __future__ import annotations

from typing import Literal

SummarizerAlgorithm = Literal["lsa", "lexrank", "luhn"]


def summarize_reviews(
    texts: list[str],
    sentences_count: int = 5,
    algorithm: SummarizerAlgorithm = "lsa",
) -> str:
    """Return an extractive summary of *texts* using the given algorithm.

    Parameters
    ----------
    texts:
        List of review strings to summarise.
    sentences_count:
        Number of sentences to include in the summary.
    algorithm:
        Summarisation algorithm — ``"lsa"`` (default), ``"lexrank"``, or ``"luhn"``.

    Returns
    -------
    str
        A single string containing the top *sentences_count* extracted sentences,
        joined with a space.  Returns an empty string if *texts* is empty.
    """
    if not texts:
        return ""

    corpus = " ".join(str(t) for t in texts if str(t).strip())
    if not corpus.strip():
        return ""

    # Ensure required NLTK data is available
    _ensure_nltk_data()

    from sumy.parsers.plaintext import PlaintextParser
    from sumy.nlp.tokenizers import Tokenizer

    _SUMMARIZERS = {
        "lsa": _get_lsa_summarizer,
        "lexrank": _get_lexrank_summarizer,
        "luhn": _get_luhn_summarizer,
    }
    _factory = _SUMMARIZERS.get(algorithm, _get_lsa_summarizer)
    summarizer = _factory()

    parser = PlaintextParser.from_string(corpus, Tokenizer("english"))
    summary_sentences = summarizer(parser.document, sentences_count=sentences_count)
    return " ".join(str(s) for s in summary_sentences)


# ---------------------------------------------------------------------------
# Internal helpers — lazy imports to avoid hard dependency at module load time
# ---------------------------------------------------------------------------

def _ensure_nltk_data() -> None:
    """Download required NLTK data packages if they are not yet available."""
    import nltk

    for resource in ("punkt", "punkt_tab"):
        try:
            nltk.data.find(f"tokenizers/{resource}")
        except LookupError:
            try:
                nltk.download(resource, quiet=True)
            except Exception:
                pass

def _get_lsa_summarizer():
    from sumy.summarizers.lsa import LsaSummarizer
    return LsaSummarizer()


def _get_lexrank_summarizer():
    from sumy.summarizers.lex_rank import LexRankSummarizer
    return LexRankSummarizer()


def _get_luhn_summarizer():
    from sumy.summarizers.luhn import LuhnSummarizer
    return LuhnSummarizer()

