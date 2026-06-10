# DigitalArchitect

Internal developer-facing knowledge assistant for architectural framework
documents. Multi-agent orchestration over a Chroma-backed RAG store, with a
FastAPI backend, Next.js chat UI, SQLite audit trail, and SendGrid-driven
escalation to a human architecture team.

## Architecture at a glance

```
┌────────────────────────┐    HTTPS / SSE    ┌──────────────────────────────┐
│ Next.js 14 chat UI     │ ─────────────────▶│ FastAPI + OpenAI Agents SDK  │
│ (login, chat, badges,  │                   │   Orchestrator               │
│  thinking indicator,   │                   │   ├─ BE / FE / DB / Infra    │
│  feedback, escalation) │                   │   ├─ Merge (multi-domain)    │
└────────────────────────┘                   │   ├─ Evaluator (5 dims)      │
                                             │   └─ Email (SendGrid)        │
                                             └───────┬──────────┬───────────┘
                                                     │          │
                                          ┌──────────▼──┐  ┌────▼────────┐
                                          │ ChromaDB    │  │ SQLite      │
                                          │ vector store│  │ audit DB    │
                                          └─────────────┘  └─────────────┘
```

## Project structure

```
DigitalArchitect/
├── backend/                 # FastAPI app, agents, tools, pipeline
├── frontend/                # Next.js 14 chat + admin UI
├── data/
│   ├── framework_docs/      # Markdown knowledge base
│   └── database/
│       ├── vector_db/       # Persistent Chroma store (created on ingest)
│       └── audit_db/        # SQLite audit DB (created on startup)
├── scripts/                 # Ingestion and file-watcher utilities
├── .env.example             # Environment variable template
├── pyproject.toml           # Python dependencies (managed by uv)
├── uv.lock                  # Locked Python dependency graph
├── .python-version          # Python version for uv
└── docker-compose.yml       # Containerised backend + frontend
```

### Key directories

| Path | Purpose |
|------|---------|
| `backend/` | FastAPI app, OpenAI Agents SDK agents, tools, pipeline, JWT auth, SSE |
| `frontend/` | Next.js 14 + Tailwind + shadcn primitives, Zustand, TanStack Query |
| `data/framework_docs/` | Markdown knowledge base organised by domain (`BE/`, `FE/`, `DB/`, `Infra/`) |
| `data/database/vector_db/` | Persistent Chroma store (OpenAI `text-embedding-3-large`) |
| `data/database/audit_db/` | SQLite audit trail (`audit.db`) with conversations and escalations |
| `scripts/` | CLI utilities for ingesting framework docs and watching for changes |

## Prerequisites

* [uv](https://docs.astral.sh/uv/) (Python project manager, used for the backend)
* Node.js 20+ and npm (for the Next.js frontend)
* Docker Desktop (optional, only for the containerised flow)

Install `uv` once on Windows:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

`uv` reads [`pyproject.toml`](pyproject.toml) and pins the resolved graph
to [`uv.lock`](uv.lock); the Python version is taken from
[`.python-version`](.python-version).

## Running locally

### 1. Configure

If `.env` does not yet exist, copy the template and fill in your secrets.
**Do not run `cp .env.example .env` if `.env` already exists** — it
will overwrite your real API keys.

```bash
# Linux / macOS / Git Bash
[ -f .env ] || cp .env.example .env

# PowerShell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Then edit `.env` and set **at minimum** `OPENAI_API_KEY` (and
`SENDGRID_API_KEY` if you want escalation emails to actually send).

Default data paths (override via env vars):

| Variable | Default |
|----------|---------|
| `CHROMA_PERSIST_DIR` | `./data/database/vector_db` |
| `SQLITE_DB_PATH` | `./data/database/audit_db/audit.db` |

### 2. Backend (uv)

```bash
# install / sync all backend dependencies into .venv from uv.lock
uv sync

# run the FastAPI app
uv run uvicorn backend.main:app --reload --port 8000
```

The audit DB is created automatically on startup, and ChromaDB is warmed
up so the first multi-domain query doesn't race on init.

If `data/database/vector_db/` is empty, ingest the knowledge base first
(see [Re-ingesting the knowledge base](#re-ingesting-the-knowledge-base)).

### 3. Frontend

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

Open `http://localhost:3000` and sign in with one of the credentials from
`AUTH_USERS` (defaults: `admin/admin123`, `dev/dev123`).

Admin users can also open `http://localhost:3000/admin` to view agent
settings and per-user usage.

### 4. Docker (one command)

```bash
docker compose up --build
```

`docker-compose.yml` builds the backend (port 8000) and frontend (port
3000), mounts `./data/database/vector_db` read-write, and persists
`data/database/audit_db/` in a named volume. The backend image installs from
[`backend/requirements.txt`](backend/requirements.txt), which is kept in
sync with `pyproject.toml`.

## Re-ingesting the knowledge base

```bash
uv run scripts/ingest_docs.py
```

This uses the versioned ingest pipeline in `backend/vector/versioned_ingest.py`
and updates `data/database/vector_db/` from `data/framework_docs/`.

To watch for file changes and ingest automatically:

```bash
uv run scripts/watch_docs.py
```

## API surface

| Method | Path | Auth |
|--------|------|------|
| `POST` | `/api/v1/auth/login` | public |
| `POST` | `/api/v1/auth/logout` | bearer |
| `GET`  | `/api/v1/auth/me` | bearer |
| `POST` | `/api/v1/chat` | bearer |
| `GET`  | `/api/v1/chat/stream?query=...&token=...` | bearer (token in query) |
| `GET`  | `/api/v1/chat/history` | bearer |
| `GET`  | `/api/v1/chat/{conversation_id}` | bearer (owner or admin) |
| `POST` | `/api/v1/feedback` | bearer (1 per conversation) |
| `GET`  | `/api/v1/documents` | bearer |
| `POST` | `/api/v1/documents/ingest` | bearer |
| `POST` | `/api/v1/documents/ingest/watch` | bearer |
| `GET`  | `/api/v1/audit/summary` | admin |
| `GET`  | `/api/v1/audit/conversations` | admin |
| `GET`  | `/api/v1/audit/conversations/{id}` | admin |
| `GET`  | `/api/v1/audit/evaluations` | admin |
| `GET`  | `/api/v1/audit/feedback` | admin |
| `GET`  | `/api/v1/audit/escalations` | admin |
| `POST` | `/api/v1/audit/escalations/{ticket_id}/resolve` | admin |
| `GET`  | `/api/v1/audit/model-performance` | admin |
| `GET`  | `/api/v1/admin/agents` | admin |
| `PUT`  | `/api/v1/admin/agents/{agent_key}` | admin |
| `GET`  | `/api/v1/admin/usage` | admin |
| `GET`  | `/framework-docs/{path}` | public (static markdown) |
| `GET`  | `/healthz` | public |

## Configuration

Every model, threshold, and integration key is environment-variable
driven (see [`backend/config.py`](backend/config.py) and
[`.env.example`](.env.example)). Models per agent are independently
configurable.

Path constants in `backend/config.py`:

| Constant | Path |
|----------|------|
| `DATA_DIR` | `data/` |
| `FRAMEWORK_DOCS_DIR` | `data/framework_docs/` |
| `DATABASE_DIR` | `data/database/` |

## Useful uv commands

| Command | Purpose |
|---------|---------|
| `uv sync` | Recreate `.venv` from `uv.lock` |
| `uv sync --upgrade` | Upgrade locked versions within constraints |
| `uv add <pkg>` | Add a runtime dependency |
| `uv add --dev <pkg>` | Add a dev-only dependency |
| `uv remove <pkg>` | Remove a dependency |
| `uv run <cmd>` | Run any command inside the project env |
| `uv run python -m backend.main` | Start the API without uvicorn reload |
| `uv lock` | Refresh `uv.lock` without installing |
| `uv tree` | Show the resolved dependency tree |
