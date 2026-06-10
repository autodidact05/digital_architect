"""Version-aware document ingestion with atomic Chroma replace."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path

from langchain_text_splitters import (
    MarkdownHeaderTextSplitter,
    RecursiveCharacterTextSplitter,
)

from backend.db import document_service
from backend.vector import chroma_store
from backend.vector.doc_identity import (
    FRAMEWORK_DOCS_DIR,
    DocumentFileMeta,
    next_version,
    resolve_file_meta,
    sha256_text,
)

logger = logging.getLogger(__name__)

# In-memory notice bus for affected doc_ids (orchestrator can poll / subscribe later).
_affected_doc_ids: set[str] = set()


@dataclass
class IngestResult:
    doc_id: str
    version: str | None
    action: str  # ingested | skipped | deprecated | deleted
    chunk_count: int = 0
    message: str = ""


def _chunk_markdown(content: str, base_metadata: dict) -> list[str]:
    """Split by markdown headers, then enforce size bounds with overlap."""
    header_splitter = MarkdownHeaderTextSplitter(
        headers_to_split_on=[("##", "section"), ("#", "title")]
    )
    pieces: list[str] = []
    for doc in header_splitter.split_text(content):
        text = doc.page_content.strip()
        if text:
            pieces.append(text)

    if not pieces:
        pieces = [content.strip()]

    recursive = RecursiveCharacterTextSplitter(
        chunk_size=1500,
        chunk_overlap=100,
        length_function=len,
    )
    final: list[str] = []
    for piece in pieces:
        if len(piece) < 200 and len(pieces) == 1:
            final.append(piece)
            continue
        if len(piece) <= 1500:
            final.append(piece)
        else:
            final.extend(recursive.split_text(piece))
    return [p for p in final if len(p.strip()) >= 50 or len(final) == 1]


def _derive_doc_type(relative_path: str) -> str:
    from backend.vector.doc_identity import STACK_PREFIXES

    stem = Path(relative_path).stem
    for prefix in STACK_PREFIXES:
        if stem.startswith(prefix):
            return stem[len(prefix) :]
    return stem


async def ingest_file(
    file_path: Path,
    *,
    ingested_by: str = "pipeline",
    change_summary: str | None = None,
    force: bool = False,
) -> IngestResult:
    """Ingest one markdown file with version tracking and atomic Chroma swap."""
    meta = resolve_file_meta(file_path)
    content = file_path.read_text(encoding="utf-8")
    version_hash = sha256_text(content)

    existing_doc = await document_service.get_document(meta.doc_id)
    active = await document_service.get_active_version(meta.doc_id)

    if active and active.version_hash == version_hash and not force:
        await document_service.record_ingestion_event(
            doc_id=meta.doc_id,
            action="skipped",
            ingested_by=ingested_by,
            version=active.version,
            version_hash=version_hash,
            change_summary="Content hash unchanged",
        )
        return IngestResult(
            doc_id=meta.doc_id,
            version=active.version,
            action="skipped",
            message="unchanged",
        )

    new_version = next_version(
        existing_doc.current_version if existing_doc else None,
        manifest_version=meta.manifest_version,
        content_changed=True,
    )

    # 1) Deprecate prior active version in SQLite BEFORE touching Chroma.
    if active:
        await document_service.deprecate_active_version(meta.doc_id)

    # 2) Delete all Chroma chunks for this doc_id (no dual-active in vector store).
    deleted = await asyncio.to_thread(chroma_store.delete_chunks_for_doc, meta.doc_id)

    chunks = _chunk_markdown(content, {})
    doc_type = _derive_doc_type(meta.relative_path)

    # 3) Insert new version chunks (only these are active in Chroma).
    chunk_count = await asyncio.to_thread(
        chroma_store.add_versioned_chunks,
        doc_id=meta.doc_id,
        version=new_version,
        version_hash=version_hash,
        domain=meta.domain,
        stack=meta.stack,
        title=meta.title,
        relative_path=meta.relative_path,
        chunks=chunks,
        doc_type=doc_type,
    )

    summary = change_summary or (
        f"Re-ingested {meta.relative_path}; replaced {deleted} prior chunks"
    )
    await document_service.record_version_and_document(
        doc_id=meta.doc_id,
        version=new_version,
        version_hash=version_hash,
        domain=meta.domain,
        stack=meta.stack,
        relative_path=meta.relative_path,
        title=meta.title,
        ingested_by=ingested_by,
        change_summary=summary,
        chunk_count=chunk_count,
    )
    await document_service.record_ingestion_event(
        doc_id=meta.doc_id,
        action="ingested",
        ingested_by=ingested_by,
        version=new_version,
        version_hash=version_hash,
        change_summary=summary,
        chunk_count=chunk_count,
    )

    _affected_doc_ids.add(meta.doc_id)
    logger.info(
        "Ingested %s version %s (%d chunks)", meta.doc_id, new_version, chunk_count
    )
    return IngestResult(
        doc_id=meta.doc_id,
        version=new_version,
        action="ingested",
        chunk_count=chunk_count,
        message=summary,
    )


async def deprecate_document(
    doc_id: str,
    *,
    ingested_by: str = "admin",
    change_summary: str | None = None,
) -> IngestResult:
    """Mark document deprecated and remove all chunks from Chroma."""
    active = await document_service.get_active_version(doc_id)
    if active:
        await document_service.deprecate_active_version(doc_id)
    removed = await asyncio.to_thread(chroma_store.delete_chunks_for_doc, doc_id)
    if active:
        await document_service.mark_version_deleted(doc_id, active.version)
    await document_service.record_ingestion_event(
        doc_id=doc_id,
        action="deprecated",
        ingested_by=ingested_by,
        version=active.version if active else None,
        change_summary=change_summary or f"Deprecated; removed {removed} chunks",
    )
    _affected_doc_ids.add(doc_id)
    return IngestResult(
        doc_id=doc_id,
        version=active.version if active else None,
        action="deprecated",
        message=change_summary or "deprecated",
    )


async def ingest_all_docs(
    *,
    ingested_by: str = "pipeline",
    docs_dir: Path | None = None,
) -> list[IngestResult]:
    root = docs_dir or FRAMEWORK_DOCS_DIR
    results: list[IngestResult] = []
    for path in sorted(root.rglob("*.md")):
        if path.name.lower() == "readme.md":
            continue
        results.append(
            await ingest_file(path, ingested_by=ingested_by)
        )
    return results


async def scan_and_ingest_changed(
    *,
    ingested_by: str = "watcher",
    docs_dir: Path | None = None,
) -> list[IngestResult]:
    """File-watcher entry: ingest only added/changed files (hash-based skip)."""
    return await ingest_all_docs(ingested_by=ingested_by, docs_dir=docs_dir)


def pop_affected_doc_ids() -> list[str]:
    ids = sorted(_affected_doc_ids)
    _affected_doc_ids.clear()
    return ids
