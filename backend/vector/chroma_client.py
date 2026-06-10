"""ChromaDB retrieval wrapper.

Reuses the existing langchain-chroma persistent store at `data/database/vector_db/` (built
by `implementation/ingest.py`) so we don't have to re-embed the 113-chunk
knowledge base. The chunks already carry `domain` metadata, so domain-aware
retrieval is just a `where={"domain": ...}` filter."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Literal

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from backend.config import settings

Domain = Literal["BE", "FE", "DB", "Infra"]


@dataclass
class RetrievedChunk:
    chunk_id: str
    content: str
    source: str
    title: str | None
    domain: str | None
    stack: str | None
    doc_id: str | None = None
    version: str | None = None
    version_label: str | None = None
    distance: float | None = None


@dataclass
class RetrievalResult:
    chunks: list[str]
    chunk_ids: list[str]
    sources: list[str]
    distances: list[float]
    raw: list[RetrievedChunk]


_vectorstore_singleton: Chroma | None = None
_vectorstore_lock = threading.Lock()


def invalidate_vectorstore_cache() -> None:
    """Clear cached LangChain Chroma client after ingest mutations."""
    global _vectorstore_singleton
    with _vectorstore_lock:
        _vectorstore_singleton = None


def _vectorstore() -> Chroma:
    """Thread-safe singleton initialiser.

    `langchain_chroma.Chroma` wraps the Rust-backed `chromadb` client, which
    raises if two threads instantiate persistent clients concurrently on the
    same on-disk path. We gate construction with a lock so the first thread
    builds the singleton while the rest wait.
    """
    global _vectorstore_singleton
    if _vectorstore_singleton is not None:
        return _vectorstore_singleton
    with _vectorstore_lock:
        if _vectorstore_singleton is None:
            embeddings = OpenAIEmbeddings(
                model=settings.embedding_model,
                api_key=settings.openai_api_key or None,
            )
            _vectorstore_singleton = Chroma(
                persist_directory=settings.chroma_persist_dir,
                embedding_function=embeddings,
                collection_name=settings.chroma_collection_name,
            )
    return _vectorstore_singleton


def warm_up() -> None:
    """Initialise the singleton at process startup to avoid race conditions."""
    _vectorstore()


def _search(
    store: Chroma,
    *,
    query: str,
    k: int,
    domain: Domain,
    stack: str | None,
) -> list[tuple]:
    clauses: list[dict] = [{"domain": domain}, {"status": "active"}]
    if stack:
        clauses.append({"stack": stack})
    chroma_filter: dict = {"$and": clauses} if len(clauses) > 1 else clauses[0]
    return store.similarity_search_with_score(
        query=query,
        k=k,
        filter=chroma_filter,
    )


def _results_to_retrieval(
    raw_results: list[tuple],
    *,
    preferred_stack: str | None,
) -> RetrievalResult:
    chunks: list[str] = []
    chunk_ids: list[str] = []
    sources: list[str] = []
    distances: list[float] = []
    raw: list[RetrievedChunk] = []

    for idx, (doc, score) in enumerate(raw_results):
        meta = doc.metadata or {}
        source = str(meta.get("source", "")).split("framework_docs")[-1].lstrip("\\/")
        doc_id = meta.get("doc_id")
        version = meta.get("version")
        version_label = (
            f"{doc_id}:{version}" if doc_id and version else None
        )
        chunk_id = str(meta.get("chunk_index", idx))
        if doc_id and version:
            chunk_id = f"{doc_id}:{version}:{chunk_id}"
        item = RetrievedChunk(
            chunk_id=chunk_id,
            content=doc.page_content,
            source=source or str(meta.get("source", "")),
            title=meta.get("title"),
            domain=meta.get("domain"),
            stack=meta.get("stack"),
            doc_id=doc_id,
            version=version,
            version_label=version_label,
            distance=float(score),
        )
        raw.append(item)

    if preferred_stack:
        preferred = [c for c in raw if c.stack == preferred_stack]
        other = [c for c in raw if c.stack != preferred_stack]
        if preferred:
            raw = preferred + other

    for idx, item in enumerate(raw):
        chunks.append(item.content)
        chunk_ids.append(item.chunk_id)
        sources.append(item.source or item.title or "unknown")
        distances.append(item.distance or 0.0)

    return RetrievalResult(
        chunks=chunks,
        chunk_ids=chunk_ids,
        sources=list(dict.fromkeys(sources)),
        distances=distances,
        raw=raw,
    )


def retrieve(
    query: str,
    domain: Domain,
    top_k: int | None = None,
    *,
    stack: str | None = None,
) -> RetrievalResult:
    """Similarity search filtered by domain and optionally by stack metadata."""
    k = top_k or settings.chroma_top_k
    store = _vectorstore()
    fetch_k = max(k * 4, 12) if stack else k

    raw_results = _search(store, query=query, k=fetch_k, domain=domain, stack=stack)
    if not raw_results:
        # Legacy collection rows may lack ``status`` metadata until re-ingested.
        legacy_filter: dict = {"domain": domain}
        if stack:
            legacy_filter = {"$and": [{"domain": domain}, {"stack": stack}]}
        raw_results = store.similarity_search_with_score(
            query=query, k=fetch_k, filter=legacy_filter
        )

    if stack and len(raw_results) < k:
        fallback = _search(store, query=query, k=fetch_k, domain=domain, stack=None)
        seen_contents = {doc.page_content for doc, _ in raw_results}
        for doc, score in fallback:
            if doc.page_content not in seen_contents:
                raw_results.append((doc, score))
                seen_contents.add(doc.page_content)
            if len(raw_results) >= fetch_k:
                break

    if stack:
        stack_first = [
            pair
            for pair in raw_results
            if (pair[0].metadata or {}).get("stack") == stack
        ]
        if stack_first:
            raw_results = stack_first + [
                pair
                for pair in raw_results
                if (pair[0].metadata or {}).get("stack") != stack
            ]

    return _results_to_retrieval(raw_results[:k], preferred_stack=stack)
