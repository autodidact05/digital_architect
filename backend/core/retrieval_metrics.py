"""Retrieval quality metrics (MRR, nDCG, keyword coverage) per query.

Logic mirrors ``evaluation/eval.py`` but operates on plain chunk text from
Chroma rather than LangChain Document objects.
"""

from __future__ import annotations

import math
import re

from pydantic import BaseModel, Field

_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "and",
        "or",
        "but",
        "in",
        "on",
        "at",
        "to",
        "for",
        "of",
        "with",
        "by",
        "from",
        "as",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "must",
        "shall",
        "can",
        "need",
        "our",
        "your",
        "how",
        "what",
        "when",
        "where",
        "which",
        "who",
        "why",
        "this",
        "that",
        "these",
        "those",
        "i",
        "we",
        "you",
        "they",
        "it",
        "my",
        "me",
        "use",
        "using",
        "into",
        "about",
    }
)


class RetrievalMetrics(BaseModel):
    mrr: float = Field(ge=0.0, le=1.0)
    ndcg: float = Field(ge=0.0, le=1.0)
    keyword_coverage: float = Field(
        ge=0.0,
        le=100.0,
        description="Percentage of extracted keywords found in top-k chunks.",
    )
    keywords_found: int = Field(ge=0)
    total_keywords: int = Field(ge=0)


def extract_keywords(query: str, max_keywords: int = 12) -> list[str]:
    """Heuristic keyword extraction from the developer query."""
    tokens = re.findall(r"[a-zA-Z][a-zA-Z0-9_+-]{2,}", query.lower())
    seen: set[str] = set()
    keywords: list[str] = []
    for tok in tokens:
        if tok in _STOPWORDS or tok in seen:
            continue
        seen.add(tok)
        keywords.append(tok)
        if len(keywords) >= max_keywords:
            break
    if not keywords:
        words = [w for w in query.lower().split() if len(w) > 2]
        keywords = list(dict.fromkeys(words))[:max_keywords]
    return keywords


def _calculate_mrr(keyword: str, chunks: list[str]) -> float:
    keyword_lower = keyword.lower()
    for rank, chunk in enumerate(chunks, start=1):
        if keyword_lower in chunk.lower():
            return 1.0 / rank
    return 0.0


def _calculate_dcg(relevances: list[int], k: int) -> float:
    dcg = 0.0
    for i in range(min(k, len(relevances))):
        dcg += relevances[i] / math.log2(i + 2)
    return dcg


def _calculate_ndcg(keyword: str, chunks: list[str], k: int) -> float:
    keyword_lower = keyword.lower()
    relevances = [
        1 if keyword_lower in chunk.lower() else 0 for chunk in chunks[:k]
    ]
    dcg = _calculate_dcg(relevances, k)
    ideal_relevances = sorted(relevances, reverse=True)
    idcg = _calculate_dcg(ideal_relevances, k)
    return dcg / idcg if idcg > 0 else 0.0


def compute_retrieval_metrics(
    query: str,
    chunks: list[str],
    *,
    k: int | None = None,
) -> RetrievalMetrics:
    """Compute MRR, nDCG, and keyword coverage for retrieved chunks."""
    if not chunks:
        return RetrievalMetrics(
            mrr=0.0,
            ndcg=0.0,
            keyword_coverage=0.0,
            keywords_found=0,
            total_keywords=0,
        )

    top_k = k or len(chunks)
    keywords = extract_keywords(query)
    if not keywords:
        return RetrievalMetrics(
            mrr=0.0,
            ndcg=0.0,
            keyword_coverage=0.0,
            keywords_found=0,
            total_keywords=0,
        )

    mrr_scores = [_calculate_mrr(kw, chunks) for kw in keywords]
    ndcg_scores = [_calculate_ndcg(kw, chunks, top_k) for kw in keywords]
    avg_mrr = sum(mrr_scores) / len(mrr_scores)
    avg_ndcg = sum(ndcg_scores) / len(ndcg_scores)
    keywords_found = sum(1 for score in mrr_scores if score > 0)
    total_keywords = len(keywords)
    keyword_coverage = (
        (keywords_found / total_keywords * 100.0) if total_keywords else 0.0
    )

    return RetrievalMetrics(
        mrr=round(avg_mrr, 4),
        ndcg=round(avg_ndcg, 4),
        keyword_coverage=round(keyword_coverage, 2),
        keywords_found=keywords_found,
        total_keywords=total_keywords,
    )
