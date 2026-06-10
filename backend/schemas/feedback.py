"""Public API schemas for the feedback endpoint."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Rating = Literal[
    "below_expectations",
    "meets_expectations",
    "exceeds_expectations",
]


class FeedbackRequest(BaseModel):
    conversation_id: str
    rating: Rating
    comment: str | None = Field(default=None, max_length=2000)


class FeedbackResponse(BaseModel):
    id: str
    conversation_id: str
    rating: Rating
    comment: str | None
