"""Centralised configuration for the DigitalArchitect backend.

All values are loaded from environment variables (with a `.env` fallback).
Models, thresholds and integration keys are intentionally swappable so the
pipeline can be reconfigured without code changes.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DATABASE_DIR = DATA_DIR / "database"
FRAMEWORK_DOCS_DIR = DATA_DIR / "framework_docs"
LOGS_DIR = PROJECT_ROOT / "logs"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_env: str = "development"
    secret_key: str = "change-me-in-production"
    jwt_expiry_hours: int = 8
    jwt_algorithm: str = "HS256"

    auth_users: str = "admin:admin123,dev:dev123"
    admin_users: str = "admin"

    openai_api_key: str = ""

    orchestrator_model: str = "gpt-4.1-mini"
    be_agent_model: str = "gpt-4.1-nano"
    fe_agent_model: str = "gpt-4.1-nano"
    db_agent_model: str = "gpt-4.1-nano"
    infra_agent_model: str = "gpt-4.1-nano"
    merge_agent_model: str = "gpt-4o"
    evaluator_model: str = "gpt-5.1"
    email_agent_model: str = "gpt-4.1-nano"

    max_tokens: int = 4096
    temperature: float = 0.1
    evaluator_max_tokens: int = 1024
    max_eval_iterations: int = 3
    max_clarification_rounds: int = 2

    chroma_persist_dir: str = str(DATABASE_DIR / "vector_db")
    chroma_collection_name: str = "langchain"
    chroma_top_k: int = 5
    embedding_model: str = "text-embedding-3-large"

    sqlite_db_path: str = str(DATABASE_DIR / "audit_db" / "audit.db")

    sendgrid_api_key: str = ""
    # Verified sender email address to use with SendGrid.
    # If empty, falls back to `email_from`.
    sendgrid_from_email: str = ""
    email_from: str = "assistant@example.com"
    email_from_name: str = "DigitalArchitect Assistant"
    architect_team_email: str = "architecture-team@example.com"

    eval_pass_threshold: float = 0.75
    eval_confidence_threshold: float = 0.6

    frontend_origin: str = "http://localhost:3000"

    # Public base URL for framework doc links (no trailing slash).
    # Defaults to the backend static mount at /framework-docs.
    framework_docs_base_url: str = "http://localhost:8000/framework-docs"

    @property
    def parsed_auth_users(self) -> dict[str, str]:
        users: dict[str, str] = {}
        for pair in self.auth_users.split(","):
            pair = pair.strip()
            if not pair or ":" not in pair:
                continue
            username, password = pair.split(":", 1)
            users[username.strip()] = password.strip()
        return users

    @property
    def admin_user_set(self) -> set[str]:
        return {u.strip() for u in self.admin_users.split(",") if u.strip()}

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.frontend_origin.split(",") if o.strip()]

    @property
    def sqlite_url(self) -> str:
        return f"sqlite+aiosqlite:///{self.sqlite_db_path}"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
