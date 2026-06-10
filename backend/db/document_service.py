"""Persistence for versioned framework documents and query audit."""

from __future__ import annotations

import json
import uuid
from datetime import datetime

from sqlalchemy import desc, select, update

from backend.db.models import (
    Document,
    DocumentVersion,
    IngestionEvent,
    QueryAuditLog,
)
from backend.db.session import AsyncSessionLocal


async def get_document(doc_id: str) -> Document | None:
    async with AsyncSessionLocal() as session:
        return await session.get(Document, doc_id)


async def get_active_version(doc_id: str) -> DocumentVersion | None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(DocumentVersion).where(
                DocumentVersion.doc_id == doc_id,
                DocumentVersion.status == "active",
            )
        )
        return result.scalar_one_or_none()


async def get_document_by_path(relative_path: str) -> Document | None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Document).where(Document.relative_path == relative_path)
        )
        return result.scalar_one_or_none()


async def list_documents(*, limit: int = 500) -> list[Document]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Document).order_by(Document.doc_id).limit(limit)
        )
        return list(result.scalars().all())


async def list_versions(doc_id: str) -> list[DocumentVersion]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(DocumentVersion)
            .where(DocumentVersion.doc_id == doc_id)
            .order_by(desc(DocumentVersion.effective_from))
        )
        return list(result.scalars().all())


async def deprecate_active_version(
    doc_id: str,
    *,
    deprecated_at: datetime | None = None,
) -> DocumentVersion | None:
    """Mark the current active version deprecated (before Chroma delete)."""
    when = deprecated_at or datetime.utcnow()
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(DocumentVersion).where(
                DocumentVersion.doc_id == doc_id,
                DocumentVersion.status == "active",
            )
        )
        row = result.scalar_one_or_none()
        if row is None:
            return None
        row.status = "deprecated"
        row.deprecated_at = when
        await session.commit()
        await session.refresh(row)
        return row


async def record_version_and_document(
    *,
    doc_id: str,
    version: str,
    version_hash: str,
    domain: str,
    stack: str,
    relative_path: str,
    title: str,
    ingested_by: str,
    change_summary: str | None,
    chunk_count: int,
) -> DocumentVersion:
    """Upsert document registry and insert new active version row."""
    now = datetime.utcnow()
    async with AsyncSessionLocal() as session:
        doc = await session.get(Document, doc_id)
        if doc is None:
            doc = Document(
                doc_id=doc_id,
                current_version=version,
                domain=domain,
                stack=stack,
                relative_path=relative_path,
                title=title,
                created_at=now,
                updated_at=now,
            )
            session.add(doc)
        else:
            doc.current_version = version
            doc.domain = domain
            doc.stack = stack
            doc.relative_path = relative_path
            doc.title = title
            doc.updated_at = now

        version_row = DocumentVersion(
            doc_id=doc_id,
            version=version,
            version_hash=version_hash,
            status="active",
            effective_from=now,
            deprecated_at=None,
            change_summary=change_summary,
            ingested_by=ingested_by,
            chunk_count=chunk_count,
            relative_path=relative_path,
        )
        session.add(version_row)
        await session.commit()
        await session.refresh(version_row)
        return version_row


async def mark_version_deleted(doc_id: str, version: str) -> None:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(DocumentVersion).where(
                DocumentVersion.doc_id == doc_id,
                DocumentVersion.version == version,
            )
        )
        row = result.scalar_one_or_none()
        if row:
            row.status = "deleted"
            row.deprecated_at = row.deprecated_at or datetime.utcnow()
        doc = await session.get(Document, doc_id)
        if doc:
            active = await session.execute(
                select(DocumentVersion).where(
                    DocumentVersion.doc_id == doc_id,
                    DocumentVersion.status == "active",
                )
            )
            if active.scalar_one_or_none() is None:
                doc.current_version = "0.0.0"
        await session.commit()


async def record_ingestion_event(
    *,
    doc_id: str,
    action: str,
    ingested_by: str,
    version: str | None = None,
    version_hash: str | None = None,
    change_summary: str | None = None,
    chunk_count: int | None = None,
) -> None:
    async with AsyncSessionLocal() as session:
        session.add(
            IngestionEvent(
                id=str(uuid.uuid4()),
                doc_id=doc_id,
                version=version,
                action=action,
                version_hash=version_hash,
                ingested_by=ingested_by,
                change_summary=change_summary,
                chunk_count=chunk_count,
            )
        )
        await session.commit()


async def record_query_audit(
    *,
    query_id: str,
    conversation_id: str | None,
    user_id: str,
    query_text: str,
    doc_versions_used: list[str],
    answer_snapshot: str | None,
) -> None:
    async with AsyncSessionLocal() as session:
        session.add(
            QueryAuditLog(
                query_id=query_id,
                conversation_id=conversation_id,
                user_id=user_id,
                query_text=query_text,
                doc_versions_used=json.dumps(doc_versions_used),
                answer_snapshot=answer_snapshot,
            )
        )
        await session.commit()


async def list_query_audit(*, limit: int = 100) -> list[QueryAuditLog]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(QueryAuditLog)
            .order_by(desc(QueryAuditLog.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())
