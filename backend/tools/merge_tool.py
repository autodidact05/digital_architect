"""Merge tool: synthesises multiple specialist drafts."""

from __future__ import annotations

import json

from backend.agents._runtime import run_agent
from backend.agents.prompt_snippets import GROUNDED_DETAIL_INSTRUCTIONS
from backend.agents.registry import build_agent
from backend.db.audit_service import record_agent_execution
from backend.schemas.agents import MergedDraft, SpecialistDraft


def _format_drafts(drafts: list[SpecialistDraft]) -> str:
    sections: list[str] = []
    for draft in drafts:
        sections.append(
            f"--- DOMAIN: {draft.domain} ---\n"
            f"answer_found: {draft.answer_found} | confidence: {draft.confidence}\n"
            f"rewritten_query: {draft.rewritten_query}\n"
            f"sources: {', '.join(draft.sources) or '(none)'}\n"
            f"chunk_ids: {', '.join(draft.retrieved_chunk_ids) or '(none)'}\n"
            f"answer:\n{draft.answer}\n"
        )
    return "\n".join(sections)


async def merge_tool(
    *,
    original_query: str,
    drafts: list[SpecialistDraft],
    conversation_id: str,
    iteration: int,
) -> MergedDraft:
    prompt = (
        f"Developer's original question:\n{original_query}\n\n"
        f"{GROUNDED_DETAIL_INSTRUCTIONS}\n\n"
        f"Specialist drafts to merge ({len(drafts)} domains):\n\n"
        f"{_format_drafts(drafts)}\n\n"
        "Preserve all code examples and schemas from the specialist drafts. "
        "Do not add material that is not already in those drafts."
    )

    agent = await build_agent("merge")
    invocation = await run_agent(agent, prompt)
    merged: MergedDraft = invocation.output

    if not merged.sources:
        merged.sources = list(
            dict.fromkeys(src for d in drafts for src in d.sources)
        )
    if not merged.retrieved_chunk_ids:
        merged.retrieved_chunk_ids = list(
            dict.fromkeys(cid for d in drafts for cid in d.retrieved_chunk_ids)
        )
    if not merged.domains_covered:
        merged.domains_covered = [d.domain for d in drafts]

    await record_agent_execution(
        conversation_id=conversation_id,
        agent_type="merge",
        model_used=invocation.model,
        iteration=iteration,
        input_summary=prompt,
        output_summary=json.dumps(
            {
                "answer": merged.answer,
                "domains_covered": merged.domains_covered,
                "has_contradictions": merged.has_contradictions,
                "all_answer_found": merged.all_answer_found,
            },
            ensure_ascii=False,
        ),
        latency_ms=invocation.latency_ms,
        input_tokens=invocation.input_tokens,
        output_tokens=invocation.output_tokens,
    )

    return merged
