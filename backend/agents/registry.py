"""Build Agents SDK agents from admin-configurable settings."""

from __future__ import annotations

from typing import TypeVar

from agents import Agent
from pydantic import BaseModel

from backend.agents.defaults import AGENT_DEFAULTS
from backend.db.agent_settings_service import get_agent_setting
from backend.schemas.agents import (
    DomainClassification,
    EmailContent,
    EvaluatorVerdict,
    MergedDraft,
    SpecialistDraft,
)

T = TypeVar("T", bound=BaseModel)

_OUTPUT_TYPES: dict[str, type[BaseModel]] = {
    "orchestrator": DomainClassification,
    "be": SpecialistDraft,
    "fe": SpecialistDraft,
    "db": SpecialistDraft,
    "infra": SpecialistDraft,
    "merge": MergedDraft,
    "evaluator": EvaluatorVerdict,
    "email": EmailContent,
}

_AGENT_NAMES: dict[str, str] = {
    "orchestrator": "OrchestratorAgent",
    "be": "BackendSpecialistAgent",
    "fe": "FrontendSpecialistAgent",
    "db": "DatabaseSpecialistAgent",
    "infra": "InfrastructureSpecialistAgent",
    "merge": "MergeAgent",
    "evaluator": "EvaluatorAgent",
    "email": "EmailAgent",
}


async def build_agent(agent_key: str) -> Agent:
    """Create an agent instance using DB overrides or defaults."""
    defaults = AGENT_DEFAULTS[agent_key]
    row = await get_agent_setting(agent_key)
    model = row.model if row else defaults["model"]
    instructions = row.system_prompt if row else defaults["system_prompt"]
    output_type = _OUTPUT_TYPES[agent_key]
    return Agent(
        name=_AGENT_NAMES[agent_key],
        instructions=instructions,
        model=model,
        output_type=output_type,
    )


def invalidate_agent_cache() -> None:
    """Hook for future in-process caching; settings reload always rebuilds."""
