"""Evaluator tool: runs the EvaluatorAgent and records the verdict."""

from __future__ import annotations

import json

from backend.agents._runtime import run_agent
from backend.agents.registry import build_agent
from backend.config import settings
from backend.db.audit_service import record_agent_execution, record_evaluation
from backend.schemas.agents import EvaluatorVerdict


def _format_chunks(chunks: list[str]) -> str:
    if not chunks:
        return "(no chunks)"
    return "\n\n---\n\n".join(
        f"[chunk {idx}]\n{chunk}" for idx, chunk in enumerate(chunks)
    )


async def evaluator_tool(
    *,
    original_query: str,
    draft_answer: str,
    retrieved_chunks: list[str],
    iteration: int,
    conversation_id: str,
    merged_answer: str | None = None,
    domains: list[str] | None = None,
) -> EvaluatorVerdict:
    merged_block = (
        f"\nMerged answer (multi-domain):\n{merged_answer}\n"
        if merged_answer
        else ""
    )
    domains_block = (
        f"Domains covered: {', '.join(domains or [])}\n" if domains else ""
    )
    prompt = (
        f"Iteration: {iteration} / {settings.max_eval_iterations}\n"
        f"EVAL_PASS_THRESHOLD: {settings.eval_pass_threshold}\n"
        f"{domains_block}"
        f"\nDeveloper's original question:\n{original_query}\n\n"
        f"Draft answer to evaluate:\n{draft_answer}\n"
        f"{merged_block}"
        f"\nRetrieved context chunks the answer should be grounded in:\n"
        f"{_format_chunks(retrieved_chunks)}\n"
    )

    agent = await build_agent("evaluator")
    invocation = await run_agent(agent, prompt)
    verdict: EvaluatorVerdict = invocation.output

    if verdict.iteration != iteration:
        verdict.iteration = iteration
    if (
        verdict.verdict == "fail"
        and iteration >= settings.max_eval_iterations
    ):
        verdict.escalate = True

    await record_agent_execution(
        conversation_id=conversation_id,
        agent_type="evaluator",
        model_used=invocation.model,
        iteration=iteration,
        input_summary=prompt,
        output_summary=json.dumps(
            verdict.model_dump(),
            ensure_ascii=False,
        ),
        latency_ms=invocation.latency_ms,
        input_tokens=invocation.input_tokens,
        output_tokens=invocation.output_tokens,
    )

    await record_evaluation(
        conversation_id=conversation_id,
        iteration=iteration,
        verdict=verdict.verdict,
        overall_score=verdict.overall_score,
        groundedness=verdict.groundedness,
        relevance=verdict.relevance,
        completeness=verdict.completeness,
        accuracy=verdict.accuracy,
        clarity=verdict.clarity,
        feedback=verdict.feedback,
        evaluator_model=invocation.model,
    )

    return verdict
