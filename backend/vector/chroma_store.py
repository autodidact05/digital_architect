"""Low-level Chroma operations for versioned chunk lifecycle."""

from __future__ import annotations

import logging
import threading
from typing import Any

from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings

from backend.config import settings
from backend.vector.chroma_client import invalidate_vectorstore_cache

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_collection = None


def _collection_client():
    global _collection
    if _collection is not None:
        return _collection
    with _lock:
        if _collection is None:
            embeddings = OpenAIEmbeddings(
                model=settings.embedding_model,
                api_key=settings.openai_api_key or None,
            )
            store = Chroma(
                persist_directory=settings.chroma_persist_dir,
                embedding_function=embeddings,
                collection_name=settings.chroma_collection_name,
            )
            _collection = store._collection
        return _collection


def delete_chunks_for_doc(doc_id: str) -> int:
    """Remove every chunk for ``doc_id`` (all versions) from Chroma."""
    coll = _collection_client()
    existing = coll.get(where={"doc_id": doc_id}, include=[])
    ids = existing.get("ids") or []
    if ids:
        coll.delete(ids=ids)
        logger.info("Deleted %d Chroma chunks for doc_id=%s", len(ids), doc_id)
    invalidate_vectorstore_cache()
    return len(ids)


def add_versioned_chunks(
    *,
    doc_id: str,
    version: str,
    version_hash: str,
    domain: str,
    stack: str,
    title: str,
    relative_path: str,
    chunks: list[str],
    doc_type: str,
) -> int:
    """Insert chunks; caller must have deleted prior chunks for this doc_id."""
    coll = _collection_client()
    ids: list[str] = []
    documents: list[str] = []
    metadatas: list[dict[str, Any]] = []

    for index, text in enumerate(chunks):
        if not text.strip():
            continue
        chunk_id = f"{doc_id}:{version}:{index}"
        ids.append(chunk_id)
        documents.append(text)
        metadatas.append(
            {
                "doc_id": doc_id,
                "version": version,
                "version_hash": version_hash,
                "domain": domain,
                "stack": stack,
                "title": title,
                "source": relative_path,
                "doc_type": doc_type,
                "chunk_index": index,
                "status": "active",
            }
        )

    if not ids:
        return 0

    embeddings = OpenAIEmbeddings(
        model=settings.embedding_model,
        api_key=settings.openai_api_key or None,
    )
    vectors = embeddings.embed_documents(documents)
    coll.add(ids=ids, documents=documents, metadatas=metadatas, embeddings=vectors)
    invalidate_vectorstore_cache()
    logger.info(
        "Inserted %d chunks for %s:%s into Chroma", len(ids), doc_id, version
    )
    return len(ids)


def reset_collection_singleton() -> None:
    global _collection
    with _lock:
        _collection = None
    invalidate_vectorstore_cache()
