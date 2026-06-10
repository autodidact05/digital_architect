"""Admin API schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class AgentSettingView(BaseModel):
    agent_key: str
    model: str
    system_prompt: str
    updated_at: datetime | None = None
    updated_by: str | None = None


class AgentSettingUpdate(BaseModel):
    model: str = Field(min_length=1, max_length=128)
    system_prompt: str = Field(min_length=10)


class UserUsageRow(BaseModel):
    user_id: str
    total_conversations: int
    completed_conversations: int
    escalated_conversations: int
    total_input_tokens: int
    total_output_tokens: int
    last_active_at: datetime | None = None
