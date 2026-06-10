"""Admin APIs for versioned framework documents and ingest pipeline."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from backend.db import document_service
from backend.middleware.auth import CurrentUser, require_admin
from backend.schemas.documents import (
    DocumentVersionView,
    DocumentView,
    IngestRequest,
    IngestResultView,
)
from backend.vector.doc_identity import FRAMEWORK_DOCS_DIR
from backend.vector.versioned_ingest import (
    deprecate_document,
    ingest_all_docs,
    ingest_file,
    pop_affected_doc_ids,
    scan_and_ingest_changed,
)

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get("", response_model=list[DocumentView])
async def list_documents(
    _: Annotated[CurrentUser, Depends(require_admin)],
) -> list[DocumentView]:
    rows = await document_service.list_documents()
    return [
        DocumentView(
            doc_id=r.doc_id,
            current_version=r.current_version,
            domain=r.domain,
            stack=r.stack,
            relative_path=r.relative_path,
            title=r.title,
            created_at=r.created_at,
            updated_at=r.updated_at,
        )
        for r in rows
    ]


@router.get("/{doc_id}/versions", response_model=list[DocumentVersionView])
async def list_versions(
    doc_id: str,
    _: Annotated[CurrentUser, Depends(require_admin)],
) -> list[DocumentVersionView]:
    rows = await document_service.list_versions(doc_id)
    if not rows:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Unknown doc_id")
    return [
        DocumentVersionView(
            doc_id=r.doc_id,
            version=r.version,
            version_hash=r.version_hash,
            status=r.status,
            effective_from=r.effective_from,
            deprecated_at=r.deprecated_at,
            change_summary=r.change_summary,
            ingested_by=r.ingested_by,
            chunk_count=r.chunk_count,
            relative_path=r.relative_path,
        )
        for r in rows
    ]


@router.post("/ingest", response_model=list[IngestResultView])
async def ingest_documents(
    payload: IngestRequest,
    user: Annotated[CurrentUser, Depends(require_admin)],
) -> list[IngestResultView]:
    ingested_by = f"admin:{user.username}"
    if payload.relative_path:
        path = FRAMEWORK_DOCS_DIR / payload.relative_path.replace("\\", "/")
        if not path.is_file():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"File not found: {payload.relative_path}",
            )
        results = [
            await ingest_file(
                path,
                ingested_by=ingested_by,
                change_summary=payload.change_summary,
                force=payload.force,
            )
        ]
    else:
        results = await ingest_all_docs(ingested_by=ingested_by)
    return [
        IngestResultView(
            doc_id=r.doc_id,
            version=r.version,
            action=r.action,
            chunk_count=r.chunk_count,
            message=r.message,
        )
        for r in results
    ]


@router.post("/ingest/watch", response_model=list[IngestResultView])
async def ingest_watch(
    user: Annotated[CurrentUser, Depends(require_admin)],
) -> list[IngestResultView]:
    """Scan framework_docs for added/changed files (hash skip) and re-ingest."""
    results = await scan_and_ingest_changed(ingested_by=f"watcher:{user.username}")
    return [
        IngestResultView(
            doc_id=r.doc_id,
            version=r.version,
            action=r.action,
            chunk_count=r.chunk_count,
            message=r.message,
        )
        for r in results
    ]


@router.post("/{doc_id}/deprecate", response_model=IngestResultView)
async def deprecate(
    doc_id: str,
    user: Annotated[CurrentUser, Depends(require_admin)],
    change_summary: str | None = None,
) -> IngestResultView:
    result = await deprecate_document(
        doc_id, ingested_by=f"admin:{user.username}", change_summary=change_summary
    )
    return IngestResultView(
        doc_id=result.doc_id,
        version=result.version,
        action=result.action,
        chunk_count=result.chunk_count,
        message=result.message,
    )


@router.get("/ingest/affected", response_model=list[str])
async def affected_doc_ids(
    _: Annotated[CurrentUser, Depends(require_admin)],
) -> list[str]:
    """Doc IDs re-ingested since last poll (orchestrator notification hook)."""
    return pop_affected_doc_ids()


