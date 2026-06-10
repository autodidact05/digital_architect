"""Specialist tool: retrieval + specialist agent invocation."""

from __future__ import annotations

import json
from typing import Literal

from backend.agents._runtime import run_agent
from backend.agents.prompt_snippets import GROUNDED_DETAIL_INSTRUCTIONS
from backend.agents.registry import build_agent
from backend.config import settings
from backend.db.audit_service import record_agent_execution
from backend.schemas.agents import SpecialistDraft
from backend.tools.retrieval_tool import retrieval_tool
from backend.vector.chroma_client import RetrievalResult

Domain = Literal["BE", "FE", "DB", "Infra"]

_DOMAIN_AGENT_KEYS: dict[Domain, str] = {
    "BE": "be",
    "FE": "fe",
    "DB": "db",
    "Infra": "infra",
}


def _format_chunks(result: RetrievalResult) -> str:
    parts: list[str] = []
    for raw_chunk in result.raw:
        header = (
            f"[chunk_id={raw_chunk.chunk_id} | doc_version={raw_chunk.version_label or 'unknown'} "
            f"| stack={raw_chunk.stack or 'unknown'} | source={raw_chunk.source} "
            f"| title={raw_chunk.title or ''}]"
        )
        parts.append(f"{header}\n{raw_chunk.content}")
    return "\n\n---\n\n".join(parts) if parts else "(no chunks retrieved)"


def _build_prompt(
    *,
    domain: Domain,
    original_query: str,
    rewritten_query: str,
    chunks_block: str,
    feedback: str | None,
) -> str:
    feedback_block = ""
    if feedback:
        feedback_block = (
            "\nEvaluator feedback from the previous iteration "
            "(address every point explicitly in your next answer):\n"
            f"{feedback}\n"
        )
    return (
        f"Domain: {domain}\n"
        f"Original developer query:\n{original_query}\n\n"
        f"Working rewritten query: {rewritten_query}\n"
        f"{feedback_block}\n"
        f"{GROUNDED_DETAIL_INSTRUCTIONS}\n\n"
        "Retrieved context chunks (use ONLY this content as your factual source):\n"
        f"{chunks_block}\n"
    )


async def specialist_tool(
    *,
    domain: Domain,
    original_query: str,
    rewritten_query: str,
    conversation_id: str,
    iteration: int,
    feedback: str | None = None,
    stack: str | None = None,
) -> tuple[SpecialistDraft, RetrievalResult]:
    """Retrieve context for `domain` then invoke the specialist agent.

    Returns the produced draft plus the raw retrieval result so the
    orchestrator can hand the same chunks to the evaluator.
    """
    retrieval_query = rewritten_query
    if stack:
        retrieval_query = f"{rewritten_query} ({stack})"

    retrieval = await retrieval_tool(
        query=retrieval_query,
        domain=domain,
        conversation_id=conversation_id,
        iteration=iteration,
        top_k=settings.chroma_top_k,
        stack=stack,
    )

    chunks_block = _format_chunks(retrieval)
    stack_block = (
        f"\nRequired technology stack for this answer: {stack}\n"
        "Do NOT describe patterns from a different stack. If retrieved chunks "
        "are for another stack, set answer_found=false.\n"
        if stack
        else ""
    )
    prompt = _build_prompt(
        domain=domain,
        original_query=original_query,
        rewritten_query=rewritten_query,
        chunks_block=chunks_block,
        feedback=feedback,
    ).replace(
        "Retrieved context chunks",
        f"{stack_block}Retrieved context chunks",
        1,
    )

    agent = await build_agent(_DOMAIN_AGENT_KEYS[domain])
    invocation = await run_agent(agent, prompt)
    draft: SpecialistDraft = invocation.output

    if not draft.retrieved_chunk_ids:
        draft.retrieved_chunk_ids = retrieval.chunk_ids
    if not draft.sources:
        draft.sources = retrieval.sources

    await record_agent_execution(
        conversation_id=conversation_id,
        agent_type=f"specialist:{domain}",
        model_used=invocation.model,
        iteration=iteration,
        input_summary=prompt,
        output_summary=json.dumps(
            {
                "answer": draft.answer,
                "answer_found": draft.answer_found,
                "confidence": draft.confidence,
                "sources": draft.sources,
            },
            ensure_ascii=False,
        ),
        latency_ms=invocation.latency_ms,
        input_tokens=invocation.input_tokens,
        output_tokens=invocation.output_tokens,
    )

    return draft, retrieval
