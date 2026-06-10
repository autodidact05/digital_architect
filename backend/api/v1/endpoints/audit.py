"""Audit endpoints (admin-only)."""

from __future__ import annotations

import json
from collections import defaultdict
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from backend.db import audit_service, document_service
from backend.middleware.auth import CurrentUser, require_admin
from backend.schemas.audit import (
    AgentExecutionView,
    ConversationDetailView,
    EscalationView,
    EvaluationView,
    FeedbackView,
    ModelPerformanceRow,
    ResolveEscalationRequest,
)
from backend.schemas.documents import QueryAuditView

router = APIRouter(prefix="/audit", tags=["audit"])


def _evaluation_view(rec) -> EvaluationView:
    return EvaluationView(
        id=rec.id,
        conversation_id=rec.conversation_id,
        iteration=rec.iteration,
        verdict=rec.verdict,
        overall_score=rec.overall_score,
        groundedness=rec.groundedness,
        relevance=rec.relevance,
        completeness=rec.completeness,
        accuracy=rec.accuracy,
        clarity=rec.clarity,
        feedback=rec.feedback,
        evaluator_model=rec.evaluator_model,
        created_at=rec.created_at,
    )


def _feedback_view(fb) -> FeedbackView:
    return FeedbackView(
        id=fb.id,
        conversation_id=fb.conversation_id,
        user_id=fb.user_id,
        rating=fb.rating,
        comment=fb.comment,
        created_at=fb.created_at,
    )


def _escalation_view(rec) -> EscalationView:
    return EscalationView(
        id=rec.id,
        conversation_id=rec.conversation_id,
        ticket_id=rec.ticket_id,
        recipient_email=rec.recipient_email,
        sendgrid_message_id=rec.sendgrid_message_id,
        email_sent_at=rec.email_sent_at,
        expert_reply=rec.expert_reply,
        resolved_at=rec.resolved_at,
        kb_ingested=rec.kb_ingested,
    )


def _agent_view(rec) -> AgentExecutionView:
    return AgentExecutionView(
        id=rec.id,
        agent_type=rec.agent_type,
        model_used=rec.model_used,
        iteration=rec.iteration,
        input_tokens=rec.input_tokens,
        output_tokens=rec.output_tokens,
        latency_ms=rec.latency_ms,
        input_summary=rec.input_summary,
        output_summary=rec.output_summary,
        created_at=rec.created_at,
    )


@router.get("/conversations")
async def list_conversations(
    _: Annotated[CurrentUser, Depends(require_admin)],
    limit: int = 100,
    offset: int = 0,
) -> list[dict[str, object]]:
    conversations = await audit_service.list_all_conversations(
        limit=limit, offset=offset
    )
    return [audit_service.conversation_to_dict(c) for c in conversations]


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailView)
async def conversation_detail(
    conversation_id: str,
    _: Annotated[CurrentUser, Depends(require_admin)],
) -> ConversationDetailView:
    conv = await audit_service.get_conversation(conversation_id)
    if conv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )
    executions = await audit_service.list_agent_executions_for(conversation_id)
    evaluations = [e for e in conv.evaluations]
    feedback = [f for f in conv.feedback]
    escalation = conv.escalation

    return ConversationDetailView(
        conversation=audit_service.conversation_to_dict(conv),
        agent_executions=[_agent_view(e) for e in executions],
        evaluations=[_evaluation_view(e) for e in evaluations],
        feedback=[_feedback_view(f) for f in feedback],
        escalation=_escalation_view(escalation) if escalation else None,
    )


@router.get("/evaluations", response_model=list[EvaluationView])
async def evaluations(
    _: Annotated[CurrentUser, Depends(require_admin)],
    limit: int = 500,
) -> list[EvaluationView]:
    return [_evaluation_view(e) for e in await audit_service.list_evaluations(limit=limit)]


@router.get("/feedback", response_model=list[FeedbackView])
async def feedback(
    _: Annotated[CurrentUser, Depends(require_admin)],
    limit: int = 500,
) -> list[FeedbackView]:
    return [_feedback_view(f) for f in await audit_service.list_feedback(limit=limit)]


@router.get("/escalations", response_model=list[EscalationView])
async def escalations(
    _: Annotated[CurrentUser, Depends(require_admin)],
    limit: int = 100,
) -> list[EscalationView]:
    return [_escalation_view(e) for e in await audit_service.list_all_escalations(limit=limit)]


@router.post("/escalations/{ticket_id}/resolve")
async def resolve_escalation(
    ticket_id: str,
    payload: ResolveEscalationRequest,
    _: Annotated[CurrentUser, Depends(require_admin)],
) -> dict[str, str]:
    result = await audit_service.resolve_escalation(ticket_id, payload.expert_answer)
    if result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Ticket not found"
        )
    return {"ticket_id": ticket_id, "status": "resolved"}


@router.get("/model-performance", response_model=list[ModelPerformanceRow])
async def model_performance(
    _: Annotated[CurrentUser, Depends(require_admin)],
) -> list[ModelPerformanceRow]:
    executions = await audit_service.list_all_agent_executions(limit=5000)
    evaluations = await audit_service.list_evaluations(limit=5000)

    counts: dict[str, int] = defaultdict(int)
    latencies: dict[str, list[int]] = defaultdict(list)
    for e in executions:
        model = e.model_used or "unknown"
        counts[model] += 1
        if e.latency_ms is not None:
            latencies[model].append(e.latency_ms)

    scores: dict[str, list[float]] = defaultdict(list)
    for ev in evaluations:
        model = ev.evaluator_model or "unknown"
        scores[model].append(ev.overall_score)

    rows: list[ModelPerformanceRow] = []
    for model in sorted(counts):
        lat = latencies[model]
        sc = scores.get(model, [])
        rows.append(
            ModelPerformanceRow(
                model=model,
                invocations=counts[model],
                avg_latency_ms=sum(lat) / len(lat) if lat else None,
                avg_overall_score=sum(sc) / len(sc) if sc else None,
            )
        )
    return rows


@router.get("/summary")
async def summary(
    _: Annotated[CurrentUser, Depends(require_admin)],
) -> dict[str, object]:
    conversations = await audit_service.list_all_conversations(limit=10000)
    evaluations = await audit_service.list_evaluations(limit=10000)
    feedback = await audit_service.list_feedback(limit=10000)

    domain_counts: dict[str, int] = defaultdict(int)
    escalated = 0
    for conv in conversations:
        if conv.status in {"escalated", "awaiting_expert"}:
            escalated += 1
        as_dict = audit_service.conversation_to_dict(conv)
        for d in as_dict["domains_classified"] or []:
            domain_counts[d] += 1

    rating_counts: dict[str, int] = defaultdict(int)
    for fb in feedback:
        rating_counts[fb.rating] += 1

    avg_score = (
        sum(e.overall_score for e in evaluations) / len(evaluations)
        if evaluations
        else None
    )
    total = len(conversations)
    escalation_rate = (escalated / total) if total else 0.0

    return {
        "total_conversations": total,
        "avg_evaluation_score": avg_score,
        "escalation_rate": escalation_rate,
        "domain_counts": domain_counts,
        "rating_counts": rating_counts,
    }


@router.get("/queries", response_model=list[QueryAuditView])
async def query_audit_log(
    _: Annotated[CurrentUser, Depends(require_admin)],
    limit: int = 100,
) -> list[QueryAuditView]:
    """Answers tied to document versions used (transparency audit)."""
    rows = await document_service.list_query_audit(limit=limit)
    out: list[QueryAuditView] = []
    for row in rows:
        versions = json.loads(row.doc_versions_used)
        out.append(
            QueryAuditView(
                query_id=row.query_id,
                conversation_id=row.conversation_id,
                user_id=row.user_id,
                query_text=row.query_text,
                doc_versions_used=versions,
                answer_snapshot=row.answer_snapshot,
                created_at=row.created_at,
            )
        )
    return out
