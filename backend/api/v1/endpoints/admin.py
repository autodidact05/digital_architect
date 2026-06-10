"""Admin endpoints: agent configuration and usage statistics."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from backend.db import audit_service
from backend.db.agent_settings_service import list_agent_settings, update_agent_setting
from backend.middleware.auth import CurrentUser, require_admin
from backend.schemas.admin import AgentSettingUpdate, AgentSettingView, UserUsageRow

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/agents", response_model=list[AgentSettingView])
async def list_agents(
    _: Annotated[CurrentUser, Depends(require_admin)],
) -> list[AgentSettingView]:
    rows = await list_agent_settings()
    return [
        AgentSettingView(
            agent_key=row.agent_key,
            model=row.model,
            system_prompt=row.system_prompt,
            updated_at=row.updated_at,
            updated_by=row.updated_by,
        )
        for row in rows
    ]


@router.put("/agents/{agent_key}", response_model=AgentSettingView)
async def update_agent(
    agent_key: str,
    payload: AgentSettingUpdate,
    user: Annotated[CurrentUser, Depends(require_admin)],
) -> AgentSettingView:
    try:
        row = await update_agent_setting(
            agent_key=agent_key,
            model=payload.model,
            system_prompt=payload.system_prompt,
            updated_by=user.username,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)
        ) from exc
    return AgentSettingView(
        agent_key=row.agent_key,
        model=row.model,
        system_prompt=row.system_prompt,
        updated_at=row.updated_at,
        updated_by=row.updated_by,
    )


@router.get("/usage", response_model=list[UserUsageRow])
async def user_usage(
    _: Annotated[CurrentUser, Depends(require_admin)],
) -> list[UserUsageRow]:
    raw = await audit_service.get_user_usage_stats()
    return [
        UserUsageRow(
            user_id=row["user_id"],
            total_conversations=row["total_conversations"],
            completed_conversations=row["completed_conversations"],
            escalated_conversations=row["escalated_conversations"],
            total_input_tokens=row["total_input_tokens"],
            total_output_tokens=row["total_output_tokens"],
            last_active_at=row["last_active_at"],
        )
        for row in raw
    ]
