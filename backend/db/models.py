"""SQLAlchemy audit tables described in AGENTS.md §8.

Schema fields and field names match the spec exactly so downstream reports
and the audit API stay aligned with the contract."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.db.session import Base


def utcnow() -> datetime:
    return datetime.utcnow()


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(String, nullable=False, index=True)
    original_query: Mapped[str] = mapped_column(Text, nullable=False)
    rewritten_query: Mapped[str | None] = mapped_column(Text)
    domains_classified: Mapped[str | None] = mapped_column(String(64))
    is_multi_domain: Mapped[bool] = mapped_column(Boolean, default=False)
    final_answer: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(32), default="completed", index=True)
    ticket_id: Mapped[str | None] = mapped_column(String(64), index=True)
    total_iterations: Mapped[int] = mapped_column(Integer, default=1)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, index=True
    )
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)
    retrieval_mrr: Mapped[float | None] = mapped_column(Float)
    retrieval_ndcg: Mapped[float | None] = mapped_column(Float)
    retrieval_keyword_coverage: Mapped[float | None] = mapped_column(Float)
    clarification_rounds: Mapped[int] = mapped_column(Integer, default=0)

    agent_executions: Mapped[list["AgentExecution"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )
    evaluations: Mapped[list["EvaluationRecord"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )
    feedback: Mapped[list["UserFeedback"]] = relationship(
        back_populates="conversation", cascade="all, delete-orphan"
    )
    escalation: Mapped["EscalationRecord | None"] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan",
        uselist=False,
    )


class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        String, ForeignKey("conversations.id"), index=True
    )
    agent_type: Mapped[str] = mapped_column(String(32), index=True)
    model_used: Mapped[str | None] = mapped_column(String(128))
    iteration: Mapped[int] = mapped_column(Integer, default=1)
    input_tokens: Mapped[int | None] = mapped_column(Integer)
    output_tokens: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    input_summary: Mapped[str | None] = mapped_column(Text)
    output_summary: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    conversation: Mapped[Conversation] = relationship(
        back_populates="agent_executions"
    )


class EvaluationRecord(Base):
    __tablename__ = "evaluation_records"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        String, ForeignKey("conversations.id"), index=True
    )
    iteration: Mapped[int] = mapped_column(Integer)
    verdict: Mapped[str] = mapped_column(String(16), index=True)
    overall_score: Mapped[float] = mapped_column(Float)
    groundedness: Mapped[float] = mapped_column(Float)
    relevance: Mapped[float] = mapped_column(Float)
    completeness: Mapped[float] = mapped_column(Float)
    accuracy: Mapped[float] = mapped_column(Float)
    clarity: Mapped[float] = mapped_column(Float)
    feedback: Mapped[str | None] = mapped_column(Text)
    evaluator_model: Mapped[str | None] = mapped_column(String(128))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    conversation: Mapped[Conversation] = relationship(back_populates="evaluations")


class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        String, ForeignKey("conversations.id"), index=True
    )
    user_id: Mapped[str] = mapped_column(String, index=True)
    rating: Mapped[str] = mapped_column(String(32), index=True)
    comment: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    conversation: Mapped[Conversation] = relationship(back_populates="feedback")


class EscalationRecord(Base):
    __tablename__ = "escalation_records"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        String, ForeignKey("conversations.id"), unique=True, index=True
    )
    ticket_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    recipient_email: Mapped[str | None] = mapped_column(String(255))
    sendgrid_message_id: Mapped[str | None] = mapped_column(String(255))
    email_sent_at: Mapped[datetime | None] = mapped_column(DateTime)
    expert_reply: Mapped[str | None] = mapped_column(Text)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime)
    kb_ingested: Mapped[bool] = mapped_column(Boolean, default=False)

    conversation: Mapped[Conversation] = relationship(back_populates="escalation")


class AgentSetting(Base):
    """Per-agent model and system prompt overrides (admin-editable)."""

    __tablename__ = "agent_settings"

    agent_key: Mapped[str] = mapped_column(String(32), primary_key=True)
    model: Mapped[str] = mapped_column(String(128), nullable=False)
    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_by: Mapped[str | None] = mapped_column(String(64))


class Document(Base):
    """Logical framework document (stable doc_id across versions)."""

    __tablename__ = "documents"

    doc_id: Mapped[str] = mapped_column(String(128), primary_key=True)
    current_version: Mapped[str] = mapped_column(String(32), nullable=False)
    domain: Mapped[str] = mapped_column(String(16), index=True)
    stack: Mapped[str] = mapped_column(String(64), index=True)
    relative_path: Mapped[str] = mapped_column(String(512), nullable=False)
    title: Mapped[str | None] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=utcnow, onupdate=utcnow
    )

    versions: Mapped[list["DocumentVersion"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class DocumentVersion(Base):
    """Immutable version row; only one ``active`` version per doc_id in Chroma."""

    __tablename__ = "document_versions"

    doc_id: Mapped[str] = mapped_column(
        String(128), ForeignKey("documents.doc_id"), primary_key=True
    )
    version: Mapped[str] = mapped_column(String(32), primary_key=True)
    version_hash: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(
        String(16), default="active", index=True
    )  # active | deprecated | deleted
    effective_from: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    deprecated_at: Mapped[datetime | None] = mapped_column(DateTime)
    change_summary: Mapped[str | None] = mapped_column(Text)
    ingested_by: Mapped[str] = mapped_column(String(64), default="pipeline")
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)
    relative_path: Mapped[str] = mapped_column(String(512), nullable=False)

    document: Mapped[Document] = relationship(back_populates="versions")


class IngestionEvent(Base):
    """Audit row for each ingest / deprecate / skip action."""

    __tablename__ = "ingestion_events"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    doc_id: Mapped[str] = mapped_column(String(128), index=True)
    version: Mapped[str | None] = mapped_column(String(32))
    action: Mapped[str] = mapped_column(String(32), index=True)
    version_hash: Mapped[str | None] = mapped_column(String(64))
    ingested_by: Mapped[str] = mapped_column(String(64))
    change_summary: Mapped[str | None] = mapped_column(Text)
    chunk_count: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class QueryAuditLog(Base):
    """Immutable record tying each answer to document versions used."""

    __tablename__ = "query_audit_log"

    query_id: Mapped[str] = mapped_column(String, primary_key=True)
    conversation_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("conversations.id"), index=True
    )
    user_id: Mapped[str] = mapped_column(String, index=True)
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    doc_versions_used: Mapped[str] = mapped_column(Text, nullable=False)
    answer_snapshot: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
