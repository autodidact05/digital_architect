"""Public API schemas for the chat endpoints."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

ChatStatus = Literal[
    "completed",
    "escalated",
    "awaiting_expert",
    "awaiting_clarification",
    "in_progress",
    "policy_blocked",
]


class RetrievalMetricsView(BaseModel):
    mrr: float
    ndcg: float
    keyword_coverage: float
    keywords_found: int = 0
    total_keywords: int = 0


class SourceLink(BaseModel):
    filename: str
    title: str
    url: str
    doc_version: str | None = None


class ChatRequest(BaseModel):
    query: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = None
    is_clarification_reply: bool = False


class EvaluationBreakdown(BaseModel):
    overall_score: float
    groundedness: float
    relevance: float
    completeness: float
    accuracy: float
    clarity: float
    iteration: int
    verdict: Literal["pass", "fail"]


class ChatResponse(BaseModel):
    conversation_id: str
    status: ChatStatus
    answer: str
    domains: list[str]
    is_multi_domain: bool
    sources: list[str]
    source_links: list[SourceLink] = Field(default_factory=list)
    retrieval_metrics: RetrievalMetricsView | None = None
    evaluation: EvaluationBreakdown | None = None
    ticket_id: str | None = None
    clarification_questions: list[str] = Field(default_factory=list)
    doc_versions_used: list[str] = Field(default_factory=list)
    architecture_team_notified: bool = False
    iterations: int
    created_at: datetime


class ConversationSummary(BaseModel):
    id: str
    original_query: str
    status: str
    domains: list[str]
    is_multi_domain: bool
    ticket_id: str | None
    created_at: datetime
    resolved_at: datetime | None
