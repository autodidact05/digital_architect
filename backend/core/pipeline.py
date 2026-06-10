"""End-to-end orchestration state machine.

This is the single source of truth for "what happens when a developer asks
a question". It is intentionally a plain Python function rather than an
SDK-driven autonomous flow because AGENTS.md §5.1 mandates that the
orchestrator never delegates control to specialist agents and that the
pipeline is deterministic and fully audited.

Flow:

    classify
       |
       v
    [single domain]  ----+
       v                  |
    specialist            |
                          |
    [multi domain]        |
       v                  |
    asyncio.gather(specialists)  -->  merge
                          |
       v                  v
       +--->  evaluator (loop, max N iterations)  --->  pass / fail
                                                        |       |
                                                        v       v
                                                   final      escalate
                                                              (email)

Every step emits a `PipelineEvent` for the SSE thinking indicator and
records an `AgentExecution` row in the audit DB.
"""

from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass
from datetime import datetime
from typing import Literal

from backend.agents._runtime import run_agent
from backend.agents.registry import build_agent
from backend.config import settings
from backend.core.retrieval_metrics import compute_retrieval_metrics
from backend.core.source_links import build_source_links, version_map_from_retrieval
from backend.core.stack_compliance import normalize_stack_compliance
from backend.core.stack_hints import merge_stack_hint
from backend.db import document_service
from backend.vector.chroma_client import RetrievalResult
from backend.vector.doc_versions import collect_doc_version_labels
from backend.core.sse import PipelineEmitter
from backend.db.audit_service import (
    create_conversation,
    get_conversation,
    record_agent_execution,
    update_conversation,
)
from backend.schemas.agents import (
    DomainClassification,
    EvaluatorVerdict,
    MergedDraft,
    SpecialistDraft,
)
from backend.schemas.chat import (
    ChatResponse,
    EvaluationBreakdown,
    RetrievalMetricsView,
)
from backend.tools.email_tool import email_tool, send_architecture_policy_notification
from backend.tools.evaluator_tool import evaluator_tool
from backend.tools.merge_tool import merge_tool
from backend.tools.specialist_tool import specialist_tool

logger = logging.getLogger(__name__)

Domain = Literal["BE", "FE", "DB", "Infra"]


@dataclass
class PipelineRun:
    conversation_id: str
    user_id: str
    query: str


async def _classify(
    *,
    query: str,
    conversation_id: str,
    emitter: PipelineEmitter,
    clarification_rounds: int = 0,
    force_proceed: bool = False,
) -> DomainClassification:
    await emitter.emit("classify", "started")
    cap_note = ""
    if force_proceed:
        cap_note = (
            "\n\nIMPORTANT: The developer has already answered clarification "
            f"questions {clarification_rounds} time(s). You MUST set "
            "needs_clarification=false and proceed with your best domain "
            "classification and rewritten_query using the information provided."
        )
    prompt = (
        "Classify the following developer question into one or more domains "
        "(BE / FE / DB / Infra) and return a DomainClassification JSON.\n\n"
        f"Question:\n{query}"
        f"{cap_note}"
    )
    orchestrator = await build_agent("orchestrator")
    invocation = await run_agent(orchestrator, prompt)
    classification: DomainClassification = invocation.output
    # Normalise is_multi_domain in case the model disagrees with len(domains)
    classification.is_multi_domain = len(classification.domains) > 1
    classification = normalize_stack_compliance(classification, query)

    await record_agent_execution(
        conversation_id=conversation_id,
        agent_type="orchestrator",
        model_used=invocation.model,
        iteration=1,
        input_summary=prompt,
        output_summary=classification.model_dump_json(),
        latency_ms=invocation.latency_ms,
        input_tokens=invocation.input_tokens,
        output_tokens=invocation.output_tokens,
    )
    await emitter.emit(
        "classify",
        "completed",
        domains=classification.domains,
        is_multi_domain=classification.is_multi_domain,
        needs_clarification=classification.needs_clarification,
        within_approved_stack=classification.within_approved_stack,
    )
    return classification


async def _run_specialists(
    *,
    classification: DomainClassification,
    original_query: str,
    conversation_id: str,
    iteration: int,
    feedback: str | None,
    emitter: PipelineEmitter,
) -> tuple[list[SpecialistDraft], list[str], list[RetrievalResult]]:
    """Fan out to every relevant specialist in parallel.

    Returns the drafts and the concatenated retrieved chunks used by the
    evaluator. Works for any subset of {BE, FE, DB, Infra}, including all
    four simultaneously.
    """
    import asyncio

    async def _one(domain: Domain) -> tuple[SpecialistDraft, list[str], RetrievalResult]:
        stack = merge_stack_hint(
            query=original_query,
            domain=domain,
            orchestrator_hint=classification.stack_hint_for(domain),
        )
        await emitter.emit(
            "specialist",
            "started",
            domain=domain,
            iteration=iteration,
            stack=stack,
        )
        draft, retrieval = await specialist_tool(
            domain=domain,
            original_query=original_query,
            rewritten_query=classification.rewritten_query,
            conversation_id=conversation_id,
            iteration=iteration,
            feedback=feedback,
            stack=stack,
        )
        await emitter.emit(
            "specialist",
            "completed",
            domain=domain,
            iteration=iteration,
            answer_found=draft.answer_found,
            confidence=draft.confidence,
            sources=draft.sources,
        )
        return draft, retrieval.chunks, retrieval

    results = await asyncio.gather(*[_one(d) for d in classification.domains])
    drafts = [r[0] for r in results]
    all_chunks: list[str] = []
    retrievals: list[RetrievalResult] = []
    for _, chunks, retrieval in results:
        all_chunks.extend(chunks)
        retrievals.append(retrieval)
    return drafts, all_chunks, retrievals


async def _maybe_merge(
    *,
    classification: DomainClassification,
    drafts: list[SpecialistDraft],
    original_query: str,
    conversation_id: str,
    iteration: int,
    emitter: PipelineEmitter,
) -> tuple[str, MergedDraft | None]:
    if not classification.is_multi_domain:
        return drafts[0].answer, None
    await emitter.emit("merge", "started", iteration=iteration)
    merged = await merge_tool(
        original_query=original_query,
        drafts=drafts,
        conversation_id=conversation_id,
        iteration=iteration,
    )
    await emitter.emit(
        "merge",
        "completed",
        iteration=iteration,
        has_contradictions=merged.has_contradictions,
        all_answer_found=merged.all_answer_found,
    )
    return merged.answer, merged


async def _evaluate(
    *,
    original_query: str,
    final_answer: str,
    retrieved_chunks: list[str],
    iteration: int,
    conversation_id: str,
    merged: MergedDraft | None,
    domains: list[str],
    emitter: PipelineEmitter,
) -> EvaluatorVerdict:
    await emitter.emit("evaluate", "started", iteration=iteration)
    verdict = await evaluator_tool(
        original_query=original_query,
        draft_answer=final_answer,
        retrieved_chunks=retrieved_chunks,
        iteration=iteration,
        conversation_id=conversation_id,
        merged_answer=merged.answer if merged else None,
        domains=domains,
    )
    await emitter.emit(
        "evaluate",
        "completed",
        iteration=iteration,
        verdict=verdict.verdict,
        overall_score=verdict.overall_score,
    )
    return verdict


def _new_ticket_id() -> str:
    return "AQ-" + uuid.uuid4().hex[:8].upper()


def _format_clarification_questions(questions: list[str]) -> str:
    if not questions:
        return (
            "I need a bit more detail before I can route your question safely. "
            "Please clarify your stack, environment, and what outcome you need."
        )
    lines = [
        "Before I search our architecture guides, I need a few details:",
        "",
    ]
    for idx, question in enumerate(questions, start=1):
        lines.append(f"{idx}. {question}")
    lines.extend(
        [
            "",
            "Reply in the chat with your answers and I'll continue.",
        ]
    )
    return "\n".join(lines)


def _metrics_view(chunks: list[str], query: str) -> RetrievalMetricsView:
    metrics = compute_retrieval_metrics(query, chunks)
    return RetrievalMetricsView(
        mrr=metrics.mrr,
        ndcg=metrics.ndcg,
        keyword_coverage=metrics.keyword_coverage,
        keywords_found=metrics.keywords_found,
        total_keywords=metrics.total_keywords,
    )


async def run_pipeline(
    *,
    user_id: str,
    query: str,
    conversation_id: str | None = None,
    emitter: PipelineEmitter | None = None,
    is_clarification_reply: bool = False,
) -> ChatResponse:
    """Run the full pipeline and return the public chat response."""
    emitter = emitter or PipelineEmitter()
    conv_id = conversation_id or str(uuid.uuid4())
    started_at = datetime.utcnow()
    effective_query = query

    existing = await get_conversation(conv_id) if conversation_id else None
    if existing and existing.status == "awaiting_clarification":
        base = existing.rewritten_query or existing.original_query
        effective_query = f"{base}\n\nDeveloper clarification:\n{query}"
        await update_conversation(
            conv_id,
            status="in_progress",
            rewritten_query=effective_query,
        )
    elif existing is None:
        await create_conversation(
            conversation_id=conv_id, user_id=user_id, original_query=query
        )
    elif is_clarification_reply and existing.status != "awaiting_clarification":
        effective_query = (
            f"{existing.original_query}\n\nAdditional context:\n{query}"
        )

    if existing is None:
        existing = await get_conversation(conv_id)

    clarification_rounds = existing.clarification_rounds if existing else 0
    at_clarification_cap = (
        clarification_rounds >= settings.max_clarification_rounds
    )

    await emitter.emit(
        "pipeline", "started", conversation_id=conv_id, query=effective_query
    )

    pipeline_start = time.perf_counter()

    try:
        classification = await _classify(
            query=effective_query,
            conversation_id=conv_id,
            emitter=emitter,
            clarification_rounds=clarification_rounds,
            force_proceed=at_clarification_cap,
        )
        if classification.needs_clarification and not at_clarification_cap:
            questions = classification.clarification_questions
            answer = _format_clarification_questions(questions)
            await update_conversation(
                conv_id,
                rewritten_query=effective_query,
                domains_classified=classification.domains,
                is_multi_domain=classification.is_multi_domain,
                final_answer=answer,
                status="awaiting_clarification",
                clarification_rounds=clarification_rounds + 1,
            )
            await emitter.emit(
                "pipeline",
                "completed",
                final_status="awaiting_clarification",
            )
            return ChatResponse(
                conversation_id=conv_id,
                status="awaiting_clarification",
                answer=answer,
                domains=list(classification.domains),
                is_multi_domain=classification.is_multi_domain,
                sources=[],
                source_links=[],
                clarification_questions=questions,
                iterations=0,
                created_at=started_at,
            )

        if classification.needs_clarification and at_clarification_cap:
            logger.info(
                "Clarification cap (%d) reached for conversation %s; proceeding",
                settings.max_clarification_rounds,
                conv_id,
            )
            await emitter.emit(
                "classify",
                "info",
                message=(
                    f"Clarification limit ({settings.max_clarification_rounds}) "
                    "reached — proceeding with best-effort answer"
                ),
            )
            classification.needs_clarification = False

        # --- Approved stack policy: no RAG; notify Architecture ---
        if not classification.within_approved_stack:
            ticket_id = _new_ticket_id()
            answer = classification.out_of_stack_developer_message or ""
            detected = classification.policy_detected_technologies
            await emitter.emit(
                "policy",
                "blocked",
                ticket_id=ticket_id,
                technologies=detected,
            )
            await send_architecture_policy_notification(
                original_query=effective_query,
                conversation_id=conv_id,
                user_id=user_id,
                ticket_id=ticket_id,
                detected_technologies=detected,
                orchestrator_reasoning=classification.reasoning,
            )
            await document_service.record_query_audit(
                query_id=str(uuid.uuid4()),
                conversation_id=conv_id,
                user_id=user_id,
                query_text=effective_query,
                doc_versions_used=[],
                answer_snapshot=answer,
            )
            await update_conversation(
                conv_id,
                rewritten_query=classification.rewritten_query,
                domains_classified=classification.domains,
                is_multi_domain=classification.is_multi_domain,
                final_answer=answer,
                status="policy_blocked",
                ticket_id=ticket_id,
                total_iterations=0,
                resolved_at=datetime.utcnow(),
            )
            await emitter.emit(
                "pipeline",
                "completed",
                final_status="policy_blocked",
                ticket_id=ticket_id,
            )
            summary_line = ""
            if answer and "Ticket" not in answer:
                summary_line = f"\n\nReference ticket: {ticket_id}"
            return ChatResponse(
                conversation_id=conv_id,
                status="policy_blocked",
                answer=answer + summary_line,
                domains=list(classification.domains),
                is_multi_domain=classification.is_multi_domain,
                sources=[],
                source_links=[],
                clarification_questions=[],
                doc_versions_used=[],
                architecture_team_notified=True,
                iterations=0,
                created_at=started_at,
            )

        await update_conversation(
            conv_id,
            rewritten_query=classification.rewritten_query,
            domains_classified=classification.domains,
            is_multi_domain=classification.is_multi_domain,
        )

        feedback: str | None = None
        feedback_history: list[EvaluatorVerdict] = []
        last_drafts: list[SpecialistDraft] = []
        last_answer: str = ""
        last_merged: MergedDraft | None = None
        last_chunks: list[str] = []
        last_verdict: EvaluatorVerdict | None = None
        last_retrievals: list[RetrievalResult] = []
        iteration = 0

        for iteration in range(1, settings.max_eval_iterations + 1):
            drafts, chunks, retrievals = await _run_specialists(
                classification=classification,
                original_query=effective_query,
                conversation_id=conv_id,
                iteration=iteration,
                feedback=feedback,
                emitter=emitter,
            )
            answer, merged = await _maybe_merge(
                classification=classification,
                drafts=drafts,
                original_query=effective_query,
                conversation_id=conv_id,
                iteration=iteration,
                emitter=emitter,
            )
            verdict = await _evaluate(
                original_query=effective_query,
                final_answer=answer,
                retrieved_chunks=chunks,
                iteration=iteration,
                conversation_id=conv_id,
                merged=merged,
                domains=classification.domains,
                emitter=emitter,
            )

            last_drafts = drafts
            last_answer = answer
            last_merged = merged
            last_chunks = chunks
            last_retrievals = retrievals
            last_verdict = verdict
            feedback_history.append(verdict)

            if verdict.verdict == "pass":
                break
            feedback = verdict.feedback or "Improve groundedness and address all parts of the question."

        assert last_verdict is not None  # at least one iteration runs

        if last_verdict.verdict == "pass":
            sources = (
                last_merged.sources
                if last_merged is not None
                else last_drafts[0].sources
            )
            metrics = _metrics_view(last_chunks, effective_query)
            doc_versions_used = collect_doc_version_labels(*last_retrievals)
            version_map = version_map_from_retrieval(last_retrievals)
            await document_service.record_query_audit(
                query_id=str(uuid.uuid4()),
                conversation_id=conv_id,
                user_id=user_id,
                query_text=effective_query,
                doc_versions_used=doc_versions_used,
                answer_snapshot=last_answer,
            )
            await update_conversation(
                conv_id,
                final_answer=last_answer,
                status="completed",
                total_iterations=iteration,
                resolved_at=datetime.utcnow(),
                retrieval_mrr=metrics.mrr,
                retrieval_ndcg=metrics.ndcg,
                retrieval_keyword_coverage=metrics.keyword_coverage,
            )
            await emitter.emit(
                "pipeline",
                "completed",
                final_status="completed",
                iteration=iteration,
            )
            return ChatResponse(
                conversation_id=conv_id,
                status="completed",
                answer=last_answer,
                domains=list(classification.domains),
                is_multi_domain=classification.is_multi_domain,
                sources=sources,
                source_links=build_source_links(
                    sources, version_by_source=version_map
                ),
                retrieval_metrics=metrics,
                doc_versions_used=doc_versions_used,
                evaluation=EvaluationBreakdown(
                    overall_score=last_verdict.overall_score,
                    groundedness=last_verdict.groundedness,
                    relevance=last_verdict.relevance,
                    completeness=last_verdict.completeness,
                    accuracy=last_verdict.accuracy,
                    clarity=last_verdict.clarity,
                    iteration=last_verdict.iteration,
                    verdict=last_verdict.verdict,
                ),
                iterations=iteration,
                created_at=started_at,
            )

        ticket_id = _new_ticket_id()
        await emitter.emit("escalate", "started", ticket_id=ticket_id)
        metrics = _metrics_view(last_chunks, effective_query)
        doc_versions_used = collect_doc_version_labels(*last_retrievals)
        version_map = version_map_from_retrieval(last_retrievals)
        await document_service.record_query_audit(
            query_id=str(uuid.uuid4()),
            conversation_id=conv_id,
            user_id=user_id,
            query_text=effective_query,
            doc_versions_used=doc_versions_used,
            answer_snapshot=last_answer,
        )
        dispatch = await email_tool(
            original_query=effective_query,
            drafts=last_drafts,
            feedback_history=feedback_history,
            ticket_id=ticket_id,
            conversation_id=conv_id,
            iteration=iteration,
        )
        await update_conversation(
            conv_id,
            status="awaiting_expert",
            ticket_id=ticket_id,
            total_iterations=iteration,
            final_answer=last_answer,
        )
        await emitter.emit(
            "escalate",
            "completed",
            ticket_id=ticket_id,
            message_id=dispatch.message_id,
            error=dispatch.error,
        )
        await emitter.emit(
            "pipeline",
            "completed",
            final_status="awaiting_expert",
            ticket_id=ticket_id,
            iteration=iteration,
        )

        escalation_message = (
            "We weren't able to confidently answer this from our internal "
            "documentation. The Architecture Team has been notified and "
            f"will respond on ticket {ticket_id}."
        )
        fail_sources = (
            last_merged.sources
            if last_merged
            else (last_drafts[0].sources if last_drafts else [])
        )
        return ChatResponse(
            conversation_id=conv_id,
            status="awaiting_expert",
            answer=escalation_message,
            domains=list(classification.domains),
            is_multi_domain=classification.is_multi_domain,
            sources=fail_sources,
            source_links=build_source_links(
                fail_sources, version_by_source=version_map
            ),
            retrieval_metrics=metrics,
            doc_versions_used=doc_versions_used,
            evaluation=EvaluationBreakdown(
                overall_score=last_verdict.overall_score,
                groundedness=last_verdict.groundedness,
                relevance=last_verdict.relevance,
                completeness=last_verdict.completeness,
                accuracy=last_verdict.accuracy,
                clarity=last_verdict.clarity,
                iteration=last_verdict.iteration,
                verdict=last_verdict.verdict,
            ),
            ticket_id=ticket_id,
            iterations=iteration,
            created_at=started_at,
        )

    except Exception:
        logger.exception("Pipeline failure for conversation %s", conv_id)
        await update_conversation(conv_id, status="failed")
        await emitter.emit("pipeline", "error", conversation_id=conv_id)
        raise
    finally:
        elapsed_ms = int((time.perf_counter() - pipeline_start) * 1000)
        logger.info(
            "pipeline complete conversation_id=%s elapsed_ms=%d", conv_id, elapsed_ms
        )
        await emitter.close()
