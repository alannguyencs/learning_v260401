"""Pure BM25 tokenizer + scorer shared by the notes-search service.

This is a self-contained port of the algorithm in
``terminologies/index/bm25.py`` (same tokenizer, stopwords, hyperparameters,
and Robertson-Spärck-Jones IDF). It is intentionally decoupled from that CLI:
the terminologies index runs as a standalone script (and from authoring skills)
with no backend on the path, so the two keep parallel copies rather than a
cross-package import. Keep them in sync if the ranking math ever changes.

Storage is minimal — callers pass per-document ``{"length", "term_freq"}`` maps
and corpus stats (avgdl, document frequency, IDF) are derived on demand, so a
persisted table can never drift from its own statistics.
"""

from __future__ import annotations

import math
import re
from typing import Dict, FrozenSet, List, Mapping, Tuple

# Standard BM25 hyperparameters (match terminologies/index/bm25.py).
K1 = 1.5
B = 0.75

STOPWORDS: FrozenSet[str] = frozenset(
    """
a an and any are as at be been being but by can did do does for from has have
having he her here him his how if in into is it its itself me more most my of
on once only or other our out over own same she should so some such than that
the their them then there these they this those through to too under until
up upon us was we were what when where which while who whom why will with
would you your yours
""".split()
)

TOKEN_RE = re.compile(r"[a-z0-9]+")
# Replace [text](url) with text so URLs don't pollute the term frequencies.
MD_LINK_RE = re.compile(r"\[([^\]]+)\]\([^)]+\)")


def tokenize(text: str) -> List[str]:
    """Lowercase, strip markdown links, keep alphanumeric tokens > 1 char."""
    text = MD_LINK_RE.sub(r"\1", text)
    return [t for t in TOKEN_RE.findall(text.lower()) if len(t) > 1 and t not in STOPWORDS]


def term_freq(tokens: List[str]) -> Dict[str, int]:
    """Count occurrences of each token."""
    tf: Dict[str, int] = {}
    for tok in tokens:
        tf[tok] = tf.get(tok, 0) + 1
    return tf


def _idf(term: str, documents: Mapping[str, dict], doc_count: int) -> float:
    n_q = sum(1 for d in documents.values() if term in d["term_freq"])
    if n_q == 0:
        return 0.0
    # Robertson-Spärck-Jones IDF, smoothed with the standard +1 so it stays
    # non-negative for terms appearing in more than half the corpus.
    return math.log((doc_count - n_q + 0.5) / (n_q + 0.5) + 1.0)


def bm25_scores(
    query: str,
    documents: Mapping[str, dict],
    *,
    k1: float = K1,
    b: float = B,
) -> List[Tuple[str, float]]:
    """Rank ``documents`` against ``query`` by BM25, best first.

    ``documents`` maps a key (e.g. note path or id) to
    ``{"length": int, "term_freq": {token: count}}``. Returns ``(key, score)``
    pairs with a positive score, sorted descending. An empty query or corpus
    yields ``[]``.
    """
    terms = tokenize(query)
    if not terms or not documents:
        return []
    doc_count = len(documents)
    total_len = sum(d["length"] for d in documents.values())
    avgdl = total_len / doc_count if doc_count else 0.0
    idf_cache = {t: _idf(t, documents, doc_count) for t in set(terms)}
    scores: List[Tuple[str, float]] = []
    for key, doc in documents.items():
        length = doc["length"]
        tf = doc["term_freq"]
        score = 0.0
        for term in terms:
            f = tf.get(term, 0)
            if f == 0:
                continue
            denom = f + k1 * (1 - b + b * length / avgdl) if avgdl else f
            score += idf_cache[term] * (f * (k1 + 1)) / denom
        if score > 0:
            scores.append((key, score))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores
