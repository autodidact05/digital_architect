"""Audit writers used by the orchestration pipeline.

Each helper opens its own short-lived session so callers can record audit
state asynchronously without holding the request-scoped session open. The
pipeline records audit rows at every step (conversation create, each agent
execution, each evaluator verdict, escalation, user feedback)."""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from typing import Any, Iterable

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.models import (
    AgentExecution,
    Conversation,
    EscalationRecord,
    EvaluationRecord,
    UserFeedback,
)
from backend.db.session import AsyncSessionLocal


def _truncate(value: str | None, limit: int = 4000) -> str | None:
    if value is None:
        return None
    return value if len(value) <= limit else value[:limit] + "...[truncated]"


async def create_conversation(
    conversation_id: str,
    user_id: str,
    original_query: str,
) -> Conversation:
    async with AsyncSessionLocal() as session:
        conv = Conversation(
            id=conversation_id,
            user_id=user_id,
            original_query=original_query,
            status="in_progress",
        )
        session.add(conv)
        await session.commit()
        await session.refresh(conv)
        return conv


async def update_conversation(
    conversation_id: str,
    *,
    rewritten_query: str | None = None,
    domains_classified: Iterable[str] | None = None,
    is_multi_domain: bool | None = None,
    final_answer: str | None = None,
    status: str | None = None,
    ticket_id: str | None = None,
    total_iterations: int | None = None,
    resolved_at: datetime | None = None,
    retrieval_mrr: float | None = None,
    retrieval_ndcg: float | None = None,
    retrieval_keyword_coverage: float | None = None,
    clarification_rounds: int | None = None,
) -> None:
    async with AsyncSessionLocal() as session:
        conv = await session.get(Conversation, conversation_id)
        if conv is None:
            return
        if rewritten_query is not None:
            conv.rewritten_query = _truncate(rewritten_query)
        if domains_classified is not None:
            conv.domains_classified = json.dumps(list(domains_classified))
        if is_multi_domain is not None:
            conv.is_multi_domain = is_multi_domain
        if final_answer is not None:
            conv.final_answer = final_answer
        if status is not None:
            conv.status = status
        if ticket_id is not None:
            conv.ticket_id = ticket_id
        if total_iterations is not None:
            conv.total_iterations = total_iterations
        if resolved_at is not None:
            conv.resolved_at = resolved_at
        if retrieval_mrr is not None:
            conv.retrieval_mrr = retrieval_mrr
        if retrieval_ndcg is not None:
            conv.retrieval_ndcg = retrieval_ndcg
        if retrieval_keyword_coverage is not None:
            conv.retrieval_keyword_coverage = retrieval_keyword_coverage
        if clarification_rounds is not None:
            conv.clarification_rounds = clarification_rounds
        await session.commit()


async def record_agent_execution(
    *,
    conversation_id: str,
    agent_type: str,
    model_used: str | None,
    iteration: int,
    input_summary: str | None,
    output_summary: str | None,
    latency_ms: int | None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
) -> None:
    async with AsyncSessionLocal() as session:
        session.add(
            AgentExecution(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                agent_type=agent_type,
                model_used=model_used,
                iteration=iteration,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms,
                input_summary=_truncate(input_summary),
                output_summary=_truncate(output_summary),
            )
        )
        await session.commit()


async def record_evaluation(
    *,
    conversation_id: str,
    iteration: int,
    verdict: str,
    overall_score: float,
    groundedness: float,
    relevance: float,
    completeness: float,
    accuracy: float,
    clarity: float,
    feedback: str | None,
    evaluator_model: str | None,
) -> None:
    async with AsyncSessionLocal() as session:
        session.add(
            EvaluationRecord(
                id=str(uuid.uuid4()),
                conversation_id=conversation_id,
                iteration=iteration,
                verdict=verdict,
                overall_score=overall_score,
                groundedness=groundedness,
                relevance=relevance,
                completeness=completeness,
                accuracy=accuracy,
                clarity=clarity,
                feedback=_truncate(feedback),
                evaluator_model=evaluator_model,
            )
        )
        await session.commit()


async def record_feedback(
    *,
    conversation_id: str,
    user_id: str,
    rating: str,
    comment: str | None,
) -> UserFeedback:
    async with AsyncSessionLocal() as session:
        fb = UserFeedback(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            user_id=user_id,
            rating=rating,
            comment=_truncate(comment),
        )
        session.add(fb)
        await session.commit()
        await session.refresh(fb)
        return fb


async def feedback_exists(conversation_id: str, user_id: str) -> bool:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserFeedback.id).where(
                UserFeedback.conversation_id == conversation_id,
                UserFeedback.user_id == user_id,
            )
        )
        return result.first() is not None


async def record_escalation(
    *,
    conversation_id: str,
    ticket_id: str,
    recipient_email: str,
    sendgrid_message_id: str | None,
    email_sent_at: datetime | None,
) -> EscalationRecord:
    async with AsyncSessionLocal() as session:
        rec = EscalationRecord(
            id=str(uuid.uuid4()),
            conversation_id=conversation_id,
            ticket_id=ticket_id,
            recipient_email=recipient_email,
            sendgrid_message_id=sendgrid_message_id,
            email_sent_at=email_sent_at,
        )
        session.add(rec)
        await session.commit()
        await session.refresh(rec)
        return rec


async def resolve_escalation(
    ticket_id: str,
    expert_reply: str,
) -> tuple[EscalationRecord, str] | None:
    """Mark an escalation resolved, attach the expert answer, and return
    `(escalation, conversation_id)`."""
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(EscalationRecord).where(EscalationRecord.ticket_id == ticket_id)
        )
        rec = result.scalar_one_or_none()
        if rec is None:
            return None
        rec.expert_reply = expert_reply
        rec.resolved_at = datetime.utcnow()
        conv = await session.get(Conversation, rec.conversation_id)
        if conv is not None:
            conv.status = "completed"
            conv.final_answer = expert_reply
            conv.resolved_at = rec.resolved_at
        await session.commit()
        await session.refresh(rec)
        return rec, rec.conversation_id


async def list_user_conversations(
    user_id: str, *, limit: int = 50
) -> list[Conversation]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(desc(Conversation.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())


async def get_conversation(conversation_id: str) -> Conversation | None:
    async with AsyncSessionLocal() as session:
        return await session.get(Conversation, conversation_id)


async def list_all_conversations(
    *, limit: int = 100, offset: int = 0
) -> list[Conversation]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(Conversation)
            .order_by(desc(Conversation.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())


async def list_all_escalations(*, limit: int = 100) -> list[EscalationRecord]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(EscalationRecord)
            .order_by(desc(EscalationRecord.email_sent_at))
            .limit(limit)
        )
        return list(result.scalars().all())


async def list_evaluations(*, limit: int = 500) -> list[EvaluationRecord]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(EvaluationRecord)
            .order_by(desc(EvaluationRecord.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())


async def list_feedback(*, limit: int = 500) -> list[UserFeedback]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(UserFeedback)
            .order_by(desc(UserFeedback.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())


async def list_agent_executions_for(
    conversation_id: str,
) -> list[AgentExecution]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AgentExecution)
            .where(AgentExecution.conversation_id == conversation_id)
            .order_by(AgentExecution.created_at)
        )
        return list(result.scalars().all())


async def list_all_agent_executions(*, limit: int = 1000) -> list[AgentExecution]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AgentExecution)
            .order_by(desc(AgentExecution.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())


def conversation_to_dict(conv: Conversation) -> dict[str, Any]:
    return {
        "id": conv.id,
        "user_id": conv.user_id,
        "original_query": conv.original_query,
        "rewritten_query": conv.rewritten_query,
        "domains_classified": json.loads(conv.domains_classified)
        if conv.domains_classified
        else [],
        "is_multi_domain": conv.is_multi_domain,
        "final_answer": conv.final_answer,
        "status": conv.status,
        "ticket_id": conv.ticket_id,
        "total_iterations": conv.total_iterations,
        "created_at": conv.created_at.isoformat() if conv.created_at else None,
        "resolved_at": conv.resolved_at.isoformat() if conv.resolved_at else None,
        "retrieval_mrr": conv.retrieval_mrr,
        "retrieval_ndcg": conv.retrieval_ndcg,
        "retrieval_keyword_coverage": conv.retrieval_keyword_coverage,
        "clarification_rounds": conv.clarification_rounds,
    }


async def get_user_usage_stats() -> list[dict[str, Any]]:
    """Aggregate per-user conversation and token usage for admin dashboards."""
    async with AsyncSessionLocal() as session:
        conv_result = await session.execute(select(Conversation))
        conversations = list(conv_result.scalars().all())

        exec_result = await session.execute(select(AgentExecution))
        executions = list(exec_result.scalars().all())

    conv_ids_by_user: dict[str, list[str]] = {}
    for conv in conversations:
        conv_ids_by_user.setdefault(conv.user_id, []).append(conv.id)

    exec_by_conv: dict[str, list[AgentExecution]] = {}
    for ex in executions:
        exec_by_conv.setdefault(ex.conversation_id, []).append(ex)

    stats: list[dict[str, Any]] = []
    for user_id, conv_ids in conv_ids_by_user.items():
        user_convs = [c for c in conversations if c.user_id == user_id]
        completed = sum(1 for c in user_convs if c.status == "completed")
        escalated = sum(
            1
            for c in user_convs
            if c.status in {"escalated", "awaiting_expert"}
        )
        input_tokens = 0
        output_tokens = 0
        for cid in conv_ids:
            for ex in exec_by_conv.get(cid, []):
                input_tokens += ex.input_tokens or 0
                output_tokens += ex.output_tokens or 0
        stats.append(
            {
                "user_id": user_id,
                "total_conversations": len(user_convs),
                "completed_conversations": completed,
                "escalated_conversations": escalated,
                "total_input_tokens": input_tokens,
                "total_output_tokens": output_tokens,
                "last_active_at": max(
                    (c.created_at for c in user_convs if c.created_at),
                    default=None,
                ),
            }
        )

    stats.sort(key=lambda row: row["total_conversations"], reverse=True)
    return stats
