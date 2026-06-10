"""ChromaDB retrieval wrapped as an async tool with audit hooks."""

from __future__ import annotations

import asyncio
import time
from functools import partial
from typing import Literal

from backend.db.audit_service import record_agent_execution
from backend.vector.chroma_client import RetrievalResult, retrieve

Domain = Literal["BE", "FE", "DB", "Infra"]


async def retrieval_tool(
    *,
    query: str,
    domain: Domain,
    conversation_id: str,
    iteration: int,
    top_k: int | None = None,
    stack: str | None = None,
) -> RetrievalResult:
    start = time.perf_counter()
    result = await asyncio.to_thread(
        partial(retrieve, query, domain, top_k, stack=stack)
    )
    elapsed_ms = int((time.perf_counter() - start) * 1000)
    await record_agent_execution(
        conversation_id=conversation_id,
        agent_type=f"retrieval:{domain}",
        model_used="chroma+text-embedding-3-large",
        iteration=iteration,
        input_summary=query,
        output_summary=(
            f"{len(result.chunks)} chunks; stack={stack or 'any'}; sources="
            + ", ".join(result.sources[:5])
        ),
        latency_ms=elapsed_ms,
    )
    return result
