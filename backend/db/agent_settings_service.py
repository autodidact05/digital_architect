"""CRUD for admin-editable agent model + system prompt settings."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy import select

from backend.agents.defaults import AGENT_DEFAULTS
from backend.db.models import AgentSetting
from backend.db.session import AsyncSessionLocal


async def seed_agent_settings() -> None:
    """Insert default rows for any agent_key not yet in the DB."""
    async with AsyncSessionLocal() as session:
        for key, defaults in AGENT_DEFAULTS.items():
            existing = await session.get(AgentSetting, key)
            if existing is None:
                session.add(
                    AgentSetting(
                        agent_key=key,
                        model=defaults["model"],
                        system_prompt=defaults["system_prompt"],
                    )
                )
        await session.commit()


async def get_agent_setting(agent_key: str) -> AgentSetting | None:
    async with AsyncSessionLocal() as session:
        return await session.get(AgentSetting, agent_key)


async def list_agent_settings() -> list[AgentSetting]:
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(AgentSetting).order_by(AgentSetting.agent_key)
        )
        return list(result.scalars().all())


async def update_agent_setting(
    *,
    agent_key: str,
    model: str,
    system_prompt: str,
    updated_by: str,
) -> AgentSetting:
    if agent_key not in AGENT_DEFAULTS:
        raise ValueError(f"Unknown agent key: {agent_key}")
    async with AsyncSessionLocal() as session:
        row = await session.get(AgentSetting, agent_key)
        if row is None:
            row = AgentSetting(
                agent_key=agent_key,
                model=model,
                system_prompt=system_prompt,
                updated_by=updated_by,
            )
            session.add(row)
        else:
            row.model = model
            row.system_prompt = system_prompt
            row.updated_by = updated_by
            row.updated_at = datetime.utcnow()
        await session.commit()
        await session.refresh(row)
    return row
