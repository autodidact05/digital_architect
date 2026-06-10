"""FastAPI app factory + entrypoint."""

from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.api.v1.router import api_router
from backend.config import FRAMEWORK_DOCS_DIR, settings
from backend.db.agent_settings_service import seed_agent_settings
from backend.db.session import init_db
from backend.middleware.auth import init_user_store
from backend.middleware.logging import configure_logging
from backend.vector.chroma_client import warm_up as warm_vector_store

logger = logging.getLogger(__name__)


def _validate_openai_key() -> None:
    key = (settings.openai_api_key or os.environ.get("OPENAI_API_KEY") or "").strip()
    if not key or key.startswith("sk-...") or key in {"sk-", "your-key-here"}:
        logger.error(
            "OPENAI_API_KEY is missing or still set to the placeholder. "
            "Edit .env and provide a real OpenAI key before sending chat "
            "requests."
        )


@asynccontextmanager
async def lifespan(_: FastAPI):
    configure_logging()
    init_user_store()
    if settings.openai_api_key and not os.environ.get("OPENAI_API_KEY"):
        os.environ["OPENAI_API_KEY"] = settings.openai_api_key
    _validate_openai_key()
    await init_db()
    await seed_agent_settings()
    warm_vector_store()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="DigitalArchitect",
        version="1.0.0",
        description="Internal developer knowledge assistant (multi-agent RAG).",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)

    docs_dir = FRAMEWORK_DOCS_DIR
    if docs_dir.is_dir():
        app.mount(
            "/framework-docs",
            StaticFiles(directory=str(docs_dir)),
            name="framework-docs",
        )

    @app.get("/healthz", tags=["meta"])
    async def healthz() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)
