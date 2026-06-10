"""v1 API router that aggregates every endpoint module."""

from __future__ import annotations

from fastapi import APIRouter

from backend.api.v1.endpoints import admin, audit, auth, chat, documents, feedback

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(chat.router)
api_router.include_router(feedback.router)
api_router.include_router(audit.router)
api_router.include_router(admin.router)
api_router.include_router(documents.router)
