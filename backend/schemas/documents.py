"""Schemas for versioned document management APIs."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DocumentView(BaseModel):
    doc_id: str
    current_version: str
    domain: str
    stack: str
    relative_path: str
    title: str | None
    created_at: datetime
    updated_at: datetime


class DocumentVersionView(BaseModel):
    doc_id: str
    version: str
    version_hash: str
    status: str
    effective_from: datetime
    deprecated_at: datetime | None
    change_summary: str | None
    ingested_by: str
    chunk_count: int
    relative_path: str


class IngestRequest(BaseModel):
    relative_path: str | None = Field(
        default=None,
        description="Path under framework_docs/, e.g. BE/java_springboot_caching.md",
    )
    force: bool = False
    change_summary: str | None = None


class IngestResultView(BaseModel):
    doc_id: str
    version: str | None
    action: str
    chunk_count: int = 0
    message: str = ""


class QueryAuditView(BaseModel):
    query_id: str
    conversation_id: str | None
    user_id: str
    query_text: str
    doc_versions_used: list[str]
    answer_snapshot: str | None
    created_at: datetime
