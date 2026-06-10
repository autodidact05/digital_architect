"""Audit API response schemas."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class AgentExecutionView(BaseModel):
    id: str
    agent_type: str
    model_used: str | None
    iteration: int
    input_tokens: int | None
    output_tokens: int | None
    latency_ms: int | None
    input_summary: str | None
    output_summary: str | None
    created_at: datetime


class EvaluationView(BaseModel):
    id: str
    conversation_id: str
    iteration: int
    verdict: str
    overall_score: float
    groundedness: float
    relevance: float
    completeness: float
    accuracy: float
    clarity: float
    feedback: str | None
    evaluator_model: str | None
    created_at: datetime


class FeedbackView(BaseModel):
    id: str
    conversation_id: str
    user_id: str
    rating: str
    comment: str | None
    created_at: datetime


class EscalationView(BaseModel):
    id: str
    conversation_id: str
    ticket_id: str
    recipient_email: str | None
    sendgrid_message_id: str | None
    email_sent_at: datetime | None
    expert_reply: str | None
    resolved_at: datetime | None
    kb_ingested: bool


class ConversationDetailView(BaseModel):
    conversation: dict[str, Any]
    agent_executions: list[AgentExecutionView]
    evaluations: list[EvaluationView]
    feedback: list[FeedbackView]
    escalation: EscalationView | None


class ResolveEscalationRequest(BaseModel):
    expert_answer: str
    ingest_into_kb: bool = False


class ModelPerformanceRow(BaseModel):
    model: str
    invocations: int
    avg_latency_ms: float | None
    avg_overall_score: float | None
