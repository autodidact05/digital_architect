"""Shared runtime helpers for invoking OpenAI Agents SDK agents.

We deliberately keep agent invocation explicit and Python-driven (per
AGENTS.md §5.1: the orchestrator must never delegate via autonomous handoffs).
This module wraps `Runner.run` so every call returns the parsed Pydantic
output plus the model + token usage we record in the audit log.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TypeVar

from agents import Agent, Runner

T = TypeVar("T")


@dataclass
class AgentInvocation[T]:
    output: T
    model: str | None
    input_tokens: int | None
    output_tokens: int | None
    latency_ms: int


async def run_agent(agent: Agent, prompt: str) -> AgentInvocation:
    """Invoke an Agents SDK agent and return its parsed structured output."""
    start = time.perf_counter()
    result = await Runner.run(agent, prompt)
    elapsed_ms = int((time.perf_counter() - start) * 1000)

    input_tokens = 0
    output_tokens = 0
    for response in result.raw_responses or []:
        usage = getattr(response, "usage", None)
        if usage is None:
            continue
        input_tokens += int(getattr(usage, "input_tokens", 0) or 0)
        output_tokens += int(getattr(usage, "output_tokens", 0) or 0)

    model_name: str | None = None
    if isinstance(agent.model, str):
        model_name = agent.model

    return AgentInvocation(
        output=result.final_output,
        model=model_name,
        input_tokens=input_tokens or None,
        output_tokens=output_tokens or None,
        latency_ms=elapsed_ms,
    )
