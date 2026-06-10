"""Helpers for document version transparency in answers."""

from __future__ import annotations

from backend.vector.chroma_client import RetrievedChunk, RetrievalResult


def collect_doc_version_labels(
    *results: RetrievalResult,
) -> list[str]:
    """Unique sorted doc_id:version labels from retrieval results."""
    seen: set[str] = set()
    for result in results:
        for chunk in result.raw:
            label = chunk.version_label
            if label:
                seen.add(label)
            elif chunk.doc_id and chunk.version:
                seen.add(f"{chunk.doc_id}:{chunk.version}")
    return sorted(seen)
