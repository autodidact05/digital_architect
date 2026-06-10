"""Chat endpoints: synchronous run + SSE pipeline stream + history."""

from __future__ import annotations

import asyncio
import json
import uuid
from typing import Annotated, AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from sse_starlette.sse import EventSourceResponse

from backend.core.pipeline import run_pipeline
from backend.core.sse import PipelineEmitter, PipelineEvent
from backend.db import audit_service
from backend.middleware.auth import CurrentUser, decode_token, get_current_user
from backend.schemas.chat import (
    ChatRequest,
    ChatResponse,
    ConversationSummary,
)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def post_chat(
    request: ChatRequest,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> ChatResponse:
    return await run_pipeline(
        user_id=user.username,
        query=request.query,
        conversation_id=request.conversation_id,
        is_clarification_reply=request.is_clarification_reply,
    )


@router.get("/stream")
async def stream_chat(
    query: str,
    token: str,
    conversation_id: str | None = None,
    is_clarification_reply: bool = False,
) -> EventSourceResponse:
    """SSE pipeline stream.

    The browser EventSource API can't set custom headers, so the JWT is
    supplied as a `?token=` query parameter and decoded inline.
    """
    user = decode_token(token)
    conv_id = conversation_id or str(uuid.uuid4())
    queue: asyncio.Queue[PipelineEvent | None] = asyncio.Queue()
    emitter = PipelineEmitter(queue)

    pipeline_task = asyncio.create_task(
        run_pipeline(
            user_id=user.username,
            query=query,
            conversation_id=conv_id,
            emitter=emitter,
            is_clarification_reply=is_clarification_reply,
        )
    )

    async def event_iter() -> AsyncIterator[dict[str, str]]:
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield event.to_sse()
        finally:
            try:
                result = await pipeline_task
                final_event = PipelineEvent(
                    stage="result",
                    status="final",
                    detail=json.loads(result.model_dump_json()),
                )
                yield final_event.to_sse()
            except Exception as exc:  # noqa: BLE001
                detail = str(exc) or exc.__class__.__name__
                message = (
                    "Upstream LLM authentication failed. Check that "
                    "OPENAI_API_KEY in .env is a real key, then restart the "
                    "backend."
                    if "invalid_api_key" in detail
                    or "Incorrect API key" in detail
                    or "AuthenticationError" in detail
                    else f"Pipeline error: {detail}"
                )
                yield {
                    "event": "pipeline",
                    "data": json.dumps(
                        {
                            "stage": "pipeline",
                            "status": "error",
                            "message": message,
                            "detail": detail,
                        }
                    ),
                }

    return EventSourceResponse(event_iter())


@router.get("/history", response_model=list[ConversationSummary])
async def history(
    user: Annotated[CurrentUser, Depends(get_current_user)],
    limit: int = 50,
) -> list[ConversationSummary]:
    conversations = await audit_service.list_user_conversations(
        user.username, limit=limit
    )
    out: list[ConversationSummary] = []
    for conv in conversations:
        as_dict = audit_service.conversation_to_dict(conv)
        out.append(
            ConversationSummary(
                id=conv.id,
                original_query=conv.original_query,
                status=conv.status,
                domains=as_dict["domains_classified"],
                is_multi_domain=conv.is_multi_domain,
                ticket_id=conv.ticket_id,
                created_at=conv.created_at,
                resolved_at=conv.resolved_at,
            )
        )
    return out


@router.get("/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> dict[str, object]:
    conv = await audit_service.get_conversation(conversation_id)
    if conv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )
    if conv.user_id != user.username and "admin" not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed to view this conversation",
        )
    return audit_service.conversation_to_dict(conv)
