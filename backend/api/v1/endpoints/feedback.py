"""User feedback endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from backend.db import audit_service
from backend.middleware.auth import CurrentUser, get_current_user
from backend.schemas.feedback import FeedbackRequest, FeedbackResponse

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("", response_model=FeedbackResponse)
async def submit_feedback(
    payload: FeedbackRequest,
    user: Annotated[CurrentUser, Depends(get_current_user)],
) -> FeedbackResponse:
    conv = await audit_service.get_conversation(payload.conversation_id)
    if conv is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found"
        )
    if conv.user_id != user.username and "admin" not in user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot rate someone else's conversation",
        )
    if await audit_service.feedback_exists(payload.conversation_id, user.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Feedback already submitted for this conversation",
        )

    fb = await audit_service.record_feedback(
        conversation_id=payload.conversation_id,
        user_id=user.username,
        rating=payload.rating,
        comment=payload.comment,
    )
    return FeedbackResponse(
        id=fb.id,
        conversation_id=fb.conversation_id,
        rating=fb.rating,  # type: ignore[arg-type]
        comment=fb.comment,
    )
