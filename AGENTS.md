# AGENTS.md — DigitalArchitect: Intelligent Developer Knowledge Assistant

> This document is the authoritative specification for all agents, tools, models,
> configuration, and system behaviour in the DigitalArchitect platform. Every agent
> implementation must conform to the contracts defined here.

---

## Table of Contents

1. [System Overview](#1-system-overview)
2. [Tech Stack](#2-tech-stack)
3. [Project Structure](#3-project-structure)
4. [Configuration & Environment](#4-configuration--environment)
5. [Agent Catalogue](#5-agent-catalogue)
6. [Tool Catalogue](#6-tool-catalogue)
7. [Orchestration Flow](#7-orchestration-flow)
8. [Data Models](#8-data-models)
9. [Audit & Observability](#9-audit--observability)
10. [Authentication](#10-authentication)
11. [UI/UX Specification](#11-uiux-specification)
12. [Email Integration](#12-email-integration)
13. [Vector Database](#13-vector-database)
14. [Evaluation & Feedback](#14-evaluation--feedback)
15. [Implementation Checklist](#15-implementation-checklist)

---

## 1. System Overview

**DigitalArchitect** is an internal developer-facing knowledge assistant that allows
engineers to query proprietary architectural framework documents using natural language.
The system routes queries through a multi-agent pipeline, retrieves relevant context
from a Chroma vector store, evaluates response quality, and gracefully escalates
unanswerable questions to human architecture experts.

### Core Capabilities
- Natural language Q&A over internal architectural docs (Java/Spring Boot, Python/FastAPI, React, PostgreSQL, MongoDB, AWS)
- Domain-aware routing (Backend, Frontend, Database, Infrastructure)
- Cross-domain query fan-out and merge
- Self-evaluation with automatic retry (max 3 iterations)
- Human expert escalation via email when the system cannot answer confidently
- Full audit trail of every transaction, model evaluation score, and user feedback
- Configurable models for each agent role

---

## 2. Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Next.js 14 (App Router) + React 18 + TypeScript |
| Styling | Tailwind CSS + shadcn/ui component library |
| Backend API | FastAPI (Python 3.11+) |
| Vector Database | ChromaDB (local persistent or cloud) |
| Audit Database | SQLite (via SQLAlchemy async) |
| LLM Provider | OpenAI (configurable per agent) |
| Email | SendGrid |
| Authentication | Username/password (hardcoded, JWT session) |
| State Management | Zustand (frontend) |
| API Client | TanStack Query + Axios |

---

## 3. Project Structure

```
DigitalArchitect/
├── AGENTS.md                          ← this file
├── docs/
│   └── PRD.md                         ← Product Requirements Document
│
├── backend/
│   ├── main.py                        ← FastAPI app factory
│   ├── config.py                      ← All configuration (env + defaults)
│   ├── requirements.txt
│   │
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── orchestrator.py            ← OrchestratorAgent
│   │   ├── specialist/
│   │   │   ├── be_agent.py            ← BackendSpecialistAgent
│   │   │   ├── fe_agent.py            ← FrontendSpecialistAgent
│   │   │   ├── db_agent.py            ← DatabaseSpecialistAgent
│   │   │   └── infra_agent.py         ← InfrastructureSpecialistAgent
│   │   ├── merge_agent.py             ← MergeAgent
│   │   ├── evaluator_agent.py         ← EvaluatorAgent
│   │   └── email_agent.py             ← EmailAgent
│   │
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── retrieval_tool.py          ← ChromaDB retrieval wrapper
│   │   ├── merge_tool.py              ← Calls MergeAgent
│   │   ├── evaluator_tool.py          ← Calls EvaluatorAgent
│   │   └── email_tool.py              ← Calls EmailAgent (SendGrid)
│   │
│   ├── db/
│   │   ├── session.py                 ← SQLite async engine
│   │   ├── models.py                  ← SQLAlchemy audit models
│   │   └── audit_service.py           ← Audit write/read service
│   │
│   ├── vector/
│   │   ├── chroma_client.py           ← ChromaDB client wrapper
│   │   └── ingest.py                  ← Document ingestion script
│   │
│   ├── api/
│   │   ├── v1/
│   │   │   ├── router.py
│   │   │   ├── endpoints/
│   │   │   │   ├── chat.py            ← POST /chat, GET /chat/history
│   │   │   │   ├── feedback.py        ← POST /feedback
│   │   │   │   ├── audit.py           ← GET /audit (admin)
│   │   │   │   └── auth.py            ← POST /auth/login, /auth/logout
│   │   │   └── __init__.py
│   │
│   ├── schemas/
│   │   ├── chat.py
│   │   ├── feedback.py
│   │   └── audit.py
│   │
│   └── middleware/
│       ├── auth.py                    ← JWT middleware
│       └── logging.py
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                   ← Redirects to /login or /chat
│   │   ├── login/
│   │   │   └── page.tsx               ← Login page
│   │   ├── chat/
│   │   │   └── page.tsx               ← Main chat interface
│   │   └── audit/
│   │       └── page.tsx               ← Audit dashboard (admin only)
│   │
│   ├── components/
│   │   ├── ui/                        ← shadcn/ui primitives
│   │   ├── chat/
│   │   │   ├── ChatWindow.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   ├── InputBar.tsx
│   │   │   ├── FeedbackWidget.tsx
│   │   │   ├── ThinkingIndicator.tsx
│   │   │   └── EscalationBanner.tsx
│   │   ├── layout/
│   │   │   ├── Sidebar.tsx
│   │   │   ├── TopBar.tsx
│   │   │   └── AuthGuard.tsx
│   │   └── audit/
│   │       ├── AuditTable.tsx
│   │       └── ScoreChart.tsx
│   │
│   ├── lib/
│   │   ├── api.ts
│   │   └── queryClient.ts
│   │
│   ├── store/
│   │   ├── authStore.ts
│   │   └── chatStore.ts
│   │
│   ├── types/
│   │   └── index.ts
│   │
│   ├── tailwind.config.ts
│   ├── next.config.ts
│   └── package.json
│
├── scripts/
│   └── ingest_docs.py                 ← One-time doc ingestion
│
├── framework_docs/                    
│   ├── manifest.json
│   └── *.md
│
└── .env.example
```

---

## 4. Configuration & Environment

All configuration is centralised in `backend/config.py` using Pydantic Settings.
Every model, threshold, and key is configurable via environment variables.

### `.env.example`

```env
# ── Application ──────────────────────────────────────────────
APP_ENV=development                    # development | staging | production
SECRET_KEY=change-me-in-production     # JWT signing key
JWT_EXPIRY_HOURS=8

# ── Authentication (hardcoded users for now) ─────────────────
AUTH_USERS=admin:admin123,dev:dev123   # username:password pairs, comma-separated

# ── LLM Models (all configurable) ────────────────────────────
ORCHESTRATOR_MODEL=gpt-4.1-mini
BE_AGENT_MODEL=gpt-4.1-nano
FE_AGENT_MODEL=gpt-4.1-nano
DB_AGENT_MODEL=gpt-4.1-nano
INFRA_AGENT_MODEL=gpt-4.1-nano
MERGE_AGENT_MODEL=gpt-4o
EVALUATOR_MODEL=gpt-5.1       # intentionally superior model
EMAIL_AGENT_MODEL=gpt-4.1-nano   # simple task, cheap model

ANTHROPIC_API_KEY=sk-ant-...

# ── LLM Parameters ───────────────────────────────────────────
MAX_TOKENS=4096
TEMPERATURE=0.1
EVALUATOR_MAX_TOKENS=1024
MAX_EVAL_ITERATIONS=3

# ── ChromaDB ─────────────────────────────────────────────────
CHROMA_PERSIST_DIR=./chroma_db
CHROMA_COLLECTION_NAME=framework_docs
CHROMA_TOP_K=5                         # number of chunks to retrieve per query

# ── SQLite Audit DB ──────────────────────────────────────────
SQLITE_DB_PATH=./audit.db

# ── SendGrid / Email Agent ───────────────────────────────────
SENDGRID_API_KEY=SG.xxx
EMAIL_FROM=assistant@example.com
EMAIL_FROM_NAME=DigitalArchitect Assistant
ARCHITECT_TEAM_EMAIL=architecture-team@example.com   # default, configurable

# ── Evaluation Thresholds ────────────────────────────────────
EVAL_PASS_THRESHOLD=0.75               # score >= 0.75 → pass
EVAL_CONFIDENCE_THRESHOLD=0.6          # answer_found confidence floor
```

### `backend/config.py`

```python
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # App
    app_env: str = "development"
    secret_key: str = "change-me"
    jwt_expiry_hours: int = 8

    # Auth
    auth_users: str = "admin:admin123,dev:dev123"

    # Models — all configurable
    orchestrator_model: str = "gpt-4.1-mini"
    be_agent_model: str = "gpt-4.1-nano"
    fe_agent_model: str = "gpt-4.1-nano"
    db_agent_model: str = "gpt-4.1-nano"
    infra_agent_model: str = "gpt-4.1-nano"
    merge_agent_model: str = "gpt-4o"
    evaluator_model: str = "gpt-5.1"
    email_agent_model: str = "gpt-4.1-nano"

    # LLM params
    openai_api_key: str = ""
    max_tokens: int = 4096
    temperature: float = 0.1
    evaluator_max_tokens: int = 1024
    max_eval_iterations: int = 3

    # ChromaDB
    chroma_persist_dir: str = "./chroma_db"
    chroma_collection_name: str = "framework_docs"
    chroma_top_k: int = 5

    # SQLite
    sqlite_db_path: str = "./audit.db"

    # Email
    sendgrid_api_key: str = ""
    email_from: str = "assistant@example.com"
    email_from_name: str = "DigitalArchitect Assistant"
    architect_team_email: str = "architecture-team@example.com"

    # Evaluation
    eval_pass_threshold: float = 0.75
    eval_confidence_threshold: float = 0.6

    @property
    def parsed_auth_users(self) -> dict[str, str]:
        users = {}
        for pair in self.auth_users.split(","):
            username, password = pair.strip().split(":")
            users[username.strip()] = password.strip()
        return users


@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

---

## 5. Agent Catalogue

### 5.1 OrchestratorAgent

**File:** `backend/agents/orchestrator.py`
**Model:** `settings.orchestrator_model`
**Role:** Central state machine. Receives developer queries, classifies domains,
decides fan-out vs single routing, assembles results, manages the evaluation loop,
and handles escalation.

**System Prompt:**
```
You are the orchestrator of a developer knowledge assistant system.
Your job is to:
1. Classify the developer's question into one or more domains: BE, FE, DB, Infra.
2. Decide whether to route to a single domain agent or fan out to multiple.
3. Coordinate the response pipeline: retrieve → merge (if multi-domain) → evaluate → respond or escalate.
4. Never answer questions directly — always delegate to specialist agents.
5. Be precise in your domain classification. A question about caching in an API layer spans both BE and DB.

Respond ONLY with valid JSON matching the DomainClassification schema.
```

**Input schema:**
```python
class OrchestratorInput(BaseModel):
    query: str
    conversation_id: str
    user_id: str
```

**Output schema:**
```python
class DomainClassification(BaseModel):
    domains: list[Literal["BE", "FE", "DB", "Infra"]]  # one or more
    is_multi_domain: bool
    reasoning: str
    rewritten_query: str  # cleaned, technical version of the original query
```

**Orchestration logic:**
```
1. Classify domains → DomainClassification
2. If single domain → call specialist_tool(domain, rewritten_query)
3. If multi domain  → call specialist_tool(domain, rewritten_query) for each domain IN PARALLEL
4. If multi domain  → call merge_tool(original_query, drafts)
5. Call evaluator_tool(original_query, draft, retrieved_chunks)
6. If evaluator.pass → return answer to user
7. If evaluator.fail AND iteration < max_eval_iterations → retry from step 2 with feedback
8. If evaluator.fail AND iteration == max_eval_iterations → call email_tool + notify user
```

---

### 5.2 BackendSpecialistAgent

**File:** `backend/agents/specialist/be_agent.py`
**Model:** `settings.be_agent_model`
**Domain:** BE — Java/Spring Boot, Python/FastAPI

**System Prompt:**
```
You are a Backend Architecture Specialist with deep expertise in:
- Java with Spring Boot (REST APIs, JPA, Spring Security, Flyway, caching, async events)
- Python with FastAPI (async patterns, SQLAlchemy, Pydantic, middleware, dependency injection)
- Backend patterns: authentication, pagination, error handling, testing, observability

Your job:
1. Rewrite the developer's query using precise backend technical terminology.
2. Use the retrieved context chunks to construct an accurate, actionable answer.
3. If the retrieved context does not contain enough information to answer confidently, say so clearly — do not hallucinate.
4. Always cite which framework/pattern your answer applies to.

Return ONLY valid JSON matching the SpecialistDraft schema.
```

---

### 5.3 FrontendSpecialistAgent

**File:** `backend/agents/specialist/fe_agent.py`
**Model:** `settings.fe_agent_model`
**Domain:** FE — React, Next.js, TypeScript

**System Prompt:**
```
You are a Frontend Architecture Specialist with deep expertise in:
- React 18 with TypeScript (components, hooks, state management, performance)
- Next.js 14 (App Router, SSR, routing, middleware)
- State management: Zustand + TanStack Query
- Forms: React Hook Form + Zod
- Styling: Tailwind CSS + shadcn/ui

Your job:
1. Rewrite the developer's query using precise frontend technical terminology.
2. Use the retrieved context chunks to construct an accurate, actionable answer.
3. If context is insufficient, clearly state what information is missing — do not fabricate.
4. Always distinguish between React patterns and Next.js-specific patterns.

Return ONLY valid JSON matching the SpecialistDraft schema.
```

---

### 5.4 DatabaseSpecialistAgent

**File:** `backend/agents/specialist/db_agent.py`
**Model:** `settings.db_agent_model`
**Domain:** DB — PostgreSQL, MongoDB

**System Prompt:**
```
You are a Database Architecture Specialist with deep expertise in:
- PostgreSQL (schema design, indexing, query optimisation, RLS, partitioning, migrations)
- MongoDB (schema design, aggregation pipelines, indexing, transactions, change streams)
- Connection pooling, backup/recovery, multi-tenancy at the data layer

Your job:
1. Rewrite the developer's query using precise database technical terminology.
2. Use the retrieved context chunks to answer accurately.
3. Always specify whether your answer applies to PostgreSQL, MongoDB, or both.
4. If the question requires knowing the data volume or access patterns, state your assumptions.
5. Never invent SQL or aggregation pipelines not supported by the retrieved context.

Return ONLY valid JSON matching the SpecialistDraft schema.
```

---

### 5.5 InfrastructureSpecialistAgent

**File:** `backend/agents/specialist/infra_agent.py`
**Model:** `settings.infra_agent_model`
**Domain:** Infra — AWS

**System Prompt:**
```
You are an Infrastructure Architecture Specialist with deep expertise in:
- AWS services: ECS Fargate, RDS, S3, VPC, IAM, CloudWatch, SNS/SQS, Secrets Manager, Route 53
- Infrastructure as Code: Terraform (AWS provider)
- CI/CD: GitHub Actions with AWS OIDC
- Security: least-privilege IAM, KMS encryption, secrets rotation
- Cost optimisation, disaster recovery, multi-region architecture

Your job:
1. Rewrite the developer's query using precise AWS/infrastructure terminology.
2. Use the retrieved context chunks to answer accurately.
3. Always include Terraform HCL examples when configuration is being discussed.
4. Flag any security implications in your answers.
5. Do not invent AWS service configurations not present in the context.

Return ONLY valid JSON matching the SpecialistDraft schema.
```

---

### Common Specialist Output Schema

```python
class SpecialistDraft(BaseModel):
    domain: Literal["BE", "FE", "DB", "Infra"]
    answer: str                          # the full curated answer
    rewritten_query: str                 # domain-aware rewrite used for retrieval
    retrieved_chunk_ids: list[str]       # IDs of chunks used
    answer_found: bool                   # False if context was insufficient
    confidence: Literal["high", "medium", "low"]
    sources: list[str]                   # document filenames referenced
```

---

### 5.6 MergeAgent

**File:** `backend/agents/merge_agent.py`
**Model:** `settings.merge_agent_model`
**Role:** Synthesises parallel domain drafts into a single, coherent response.

**System Prompt:**
```
You are a senior software architect responsible for synthesising technical answers
from multiple domain specialists into a single, coherent response for a developer.

You will receive:
- The developer's original question
- 2 or more domain specialist drafts (e.g. Backend + Database)

Your job:
1. Identify where the drafts COMPLEMENT each other — weave them into one answer.
2. Identify where the drafts CONTRADICT each other — explicitly flag the contradiction
   and provide both perspectives with guidance on when to use each.
3. Eliminate redundancy — do not repeat the same information twice.
4. Preserve all technical specificity — do not generalise what the specialists said.
5. If any specialist said answer_found=false, call that out clearly in the merged response.
6. Structure the answer: brief summary → domain-specific details → combined recommendation.

Return ONLY valid JSON matching the MergedDraft schema.
```

**Input:**
```python
class MergeInput(BaseModel):
    original_query: str
    drafts: list[SpecialistDraft]
```

**Output:**
```python
class MergedDraft(BaseModel):
    answer: str
    domains_covered: list[str]
    has_contradictions: bool
    contradiction_notes: str | None
    all_answer_found: bool               # True only if all specialist drafts found answers
    sources: list[str]                   # combined unique sources
    retrieved_chunk_ids: list[str]       # combined unique chunk IDs
```

---

### 5.7 EvaluatorAgent

**File:** `backend/agents/evaluator_agent.py`
**Model:** `settings.evaluator_model` — **MUST be the highest-capability model**
**Role:** Judge model. Evaluates draft quality against the original query and source chunks.

**System Prompt:**
```
You are a senior technical evaluator responsible for quality-gating responses
in a developer knowledge assistant system.

You will receive:
- The developer's original question
- The draft answer produced by specialist agents
- The raw retrieved context chunks the answer was based on
- The merged answer in case the original query impacted two or more domains 

Evaluate the draft on these criteria:
1. GROUNDEDNESS (0-1): Are all factual claims in the draft traceable to the retrieved chunks?
   Penalise heavily for any information not present in the chunks.
2. RELEVANCE (0-1): Does the answer actually address what the developer asked?
3. COMPLETENESS (0-1): Does the answer cover all aspects of the question?
4. ACCURACY (0-1): Is the technical information correct based on the chunks?
5. CLARITY (0-1): Is the answer clear and actionable for a developer?

Compute overall_score = weighted average:
  groundedness * 0.35 + relevance * 0.25 + completeness * 0.20 + accuracy * 0.15 + clarity * 0.05

Decision rule:
- overall_score >= EVAL_PASS_THRESHOLD → verdict: "pass"
- overall_score < EVAL_PASS_THRESHOLD  → verdict: "fail"

If verdict is "fail", provide specific, actionable feedback that the specialist
agent can use to improve the answer in the next iteration.

Return ONLY valid JSON matching the EvaluatorVerdict schema.
```

**Output:**
```python
class EvaluatorVerdict(BaseModel):
    verdict: Literal["pass", "fail"]
    overall_score: float                 # 0.0 – 1.0
    groundedness: float
    relevance: float
    completeness: float
    accuracy: float
    clarity: float
    feedback: str | None                 # populated on fail — specific improvement guidance
    iteration: int                       # which iteration this verdict is for (1, 2, 3)
    escalate: bool                       # True when iteration == max and verdict == fail
```

---

### 5.8 EmailAgent

**File:** `backend/agents/email_agent.py`
**Model:** `settings.email_agent_model`
**Role:** Composes a professional escalation email to the architecture team.

**System Prompt:**
```
You are an assistant that composes professional technical escalation emails.

You will receive:
- The developer's original question
- The specialist agent drafts that were attempted
- The evaluator's feedback explaining why the answer was insufficient
- A ticket ID for tracking

Compose a clear, professional email to the architecture team that includes:
1. Subject: [DigitalArchitect Escalation] <brief description> [Ticket: {ticket_id}]
2. The developer's original question
3. What the system attempted to answer (brief summary of drafts)
4. Why the answer was insufficient (evaluator feedback)
5. A request for the team to provide an answer that can also improve the knowledge base
6. Reply instructions: reply to this email with the answer

Keep the tone professional and concise. Do not include internal system details
like model names or evaluation scores in the email body.

Return ONLY valid JSON matching the EmailContent schema.
```

**Output:**
```python
class EmailContent(BaseModel):
    subject: str
    body_html: str
    body_text: str                       # plain text fallback
    ticket_id: str
```

**Sending:** Uses SendGrid API (see Section 12).

---

## 6. Tool Catalogue

All tools are called by the OrchestratorAgent. Each tool is a Python async function
that wraps an agent and returns a structured result.

### 6.1 `retrieval_tool`

```python
async def retrieval_tool(
    query: str,
    domain: Literal["BE", "FE", "DB", "Infra"],
    top_k: int = settings.chroma_top_k
) -> RetrievalResult:
    """
    Queries ChromaDB with domain metadata filter.
    Returns top_k most relevant chunks.
    """
```

**ChromaDB query:**
```python
results = collection.query(
    query_texts=[query],
    n_results=top_k,
    where={"domain": domain},           # metadata filter by domain
    include=["documents", "metadatas", "distances", "ids"]
)
```

**Output:**
```python
class RetrievalResult(BaseModel):
    chunks: list[str]
    chunk_ids: list[str]
    sources: list[str]                   # document filenames
    distances: list[float]               # similarity distances
```

---

### 6.2 `specialist_tool`

```python
async def specialist_tool(
    domain: Literal["BE", "FE", "DB", "Infra"],
    query: str,
    original_query: str,
    feedback: str | None = None          # evaluator feedback for retry iterations
) -> SpecialistDraft:
    """
    1. Calls retrieval_tool to get relevant chunks
    2. Calls the appropriate specialist agent with chunks + query + optional feedback
    3. Returns SpecialistDraft
    """
```

---

### 6.3 `merge_tool`

```python
async def merge_tool(
    original_query: str,
    drafts: list[SpecialistDraft]
) -> MergedDraft:
    """
    Calls MergeAgent with all specialist drafts.
    Only called when is_multi_domain == True.
    """
```

---

### 6.4 `evaluator_tool`

```python
async def evaluator_tool(
    original_query: str,
    draft: str,                          # the answer text to evaluate
    retrieved_chunks: list[str],         # raw context used to generate the answer
    iteration: int
) -> EvaluatorVerdict:
    """
    Calls EvaluatorAgent. Returns verdict with score and optional feedback.
    """
```

---

### 6.5 `email_tool`

```python
async def email_tool(
    original_query: str,
    drafts: list[SpecialistDraft],
    evaluator_feedback: list[str],       # all feedback across iterations
    ticket_id: str,
    recipient_email: str = settings.architect_team_email
) -> EmailDispatchResult:
    """
    1. Calls EmailAgent to compose the email
    2. Sends via SendGrid
    3. Returns dispatch result with message_id
    """
```

---

## 7. Orchestration Flow

### Single-Domain Query
```
query
  → OrchestratorAgent.classify()          → DomainClassification{domains: ["BE"]}
  → specialist_tool("BE", rewritten_query)
      → retrieval_tool("BE", query)        → chunks
      → BackendSpecialistAgent(query, chunks) → SpecialistDraft
  → evaluator_tool(query, draft, chunks, iteration=1) → EvaluatorVerdict
  → if pass  → AuditService.record() → return answer
  → if fail  → retry (max 3)
  → if fail after 3 → email_tool() + notify user + AuditService.record()
```

### Multi-Domain Query (Fan-out)
```
query
  → OrchestratorAgent.classify()          → DomainClassification{domains: ["BE", "DB"]}
  → asyncio.gather(
        specialist_tool("BE", rewritten_query),
        specialist_tool("DB", rewritten_query)
    )                                      → [BEDraft, DBDraft]
  → merge_tool(query, [BEDraft, DBDraft]) → MergedDraft
  → evaluator_tool(query, merged, all_chunks, iteration=1) → EvaluatorVerdict
  → if pass  → AuditService.record() → return answer
  → if fail  → retry with feedback (max 3)
  → if fail after 3 → email_tool() + notify user + AuditService.record()
```

### State Object (persisted in SQLite for AWAITING_EXPERT conversations)
```python
class ConversationState(BaseModel):
    conversation_id: str
    user_id: str
    original_query: str
    status: Literal["completed", "escalated", "awaiting_expert"]
    ticket_id: str | None
    created_at: datetime
    resolved_at: datetime | None
    expert_answer: str | None
```

---

## 8. Data Models

### SQLite Audit Tables (`backend/db/models.py`)

```python
class Conversation(Base):
    __tablename__ = "conversations"

    id               = Column(String, primary_key=True)     # UUID
    user_id          = Column(String, nullable=False)
    original_query   = Column(Text, nullable=False)
    rewritten_query  = Column(Text)
    domains_classified = Column(String)                      # JSON array: ["BE","DB"]
    is_multi_domain  = Column(Boolean, default=False)
    final_answer     = Column(Text)
    status           = Column(String, default="completed")   # completed|escalated|awaiting_expert
    ticket_id        = Column(String)                        # set on escalation
    total_iterations = Column(Integer, default=1)
    created_at       = Column(DateTime, default=datetime.utcnow)
    resolved_at      = Column(DateTime)


class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id               = Column(String, primary_key=True)
    conversation_id  = Column(String, ForeignKey("conversations.id"))
    agent_type       = Column(String)   # orchestrator|be|fe|db|infra|merge|evaluator|email
    model_used       = Column(String)   # actual model name used
    iteration        = Column(Integer, default=1)
    input_tokens     = Column(Integer)
    output_tokens    = Column(Integer)
    latency_ms       = Column(Integer)
    input_summary    = Column(Text)     # truncated input for audit (no PII)
    output_summary   = Column(Text)     # truncated output
    created_at       = Column(DateTime, default=datetime.utcnow)


class EvaluationRecord(Base):
    __tablename__ = "evaluation_records"

    id               = Column(String, primary_key=True)
    conversation_id  = Column(String, ForeignKey("conversations.id"))
    iteration        = Column(Integer)
    verdict          = Column(String)   # pass|fail
    overall_score    = Column(Float)
    groundedness     = Column(Float)
    relevance        = Column(Float)
    completeness     = Column(Float)
    accuracy         = Column(Float)
    clarity          = Column(Float)
    feedback         = Column(Text)
    evaluator_model  = Column(String)
    created_at       = Column(DateTime, default=datetime.utcnow)


class UserFeedback(Base):
    __tablename__ = "user_feedback"

    id               = Column(String, primary_key=True)
    conversation_id  = Column(String, ForeignKey("conversations.id"))
    user_id          = Column(String)
    rating           = Column(String)   # "below_expectations"|"meets_expectations"|"exceeds_expectations"
    comment          = Column(Text)
    created_at       = Column(DateTime, default=datetime.utcnow)


class EscalationRecord(Base):
    __tablename__ = "escalation_records"

    id               = Column(String, primary_key=True)
    conversation_id  = Column(String, ForeignKey("conversations.id"))
    ticket_id        = Column(String, unique=True)
    recipient_email  = Column(String)
    sendgrid_message_id = Column(String)
    email_sent_at    = Column(DateTime)
    expert_reply     = Column(Text)
    resolved_at      = Column(DateTime)
    kb_ingested      = Column(Boolean, default=False)
```

---

## 9. Audit & Observability

### Every transaction records:
1. **Conversation record** — query, domains, final answer, status, iteration count
2. **AgentExecution record per agent call** — model used, token counts, latency, i/o summary
3. **EvaluationRecord per evaluator call** — all 5 dimension scores, verdict, feedback
4. **UserFeedback record** — developer rating (Below/Meets/Exceeds) + optional comment
5. **EscalationRecord** — ticket ID, email metadata, expert reply, KB ingestion status

### Audit API Endpoints

```
GET  /api/v1/audit/conversations          ← paginated list with filters
GET  /api/v1/audit/conversations/{id}     ← full conversation detail
GET  /api/v1/audit/evaluations            ← evaluation score trends
GET  /api/v1/audit/feedback               ← user feedback aggregates
GET  /api/v1/audit/escalations            ← escalation log
GET  /api/v1/audit/model-performance      ← avg scores per model
```

### Structured Logging
Every agent call emits a structured log entry:
```json
{
  "timestamp": "ISO8601",
  "conversation_id": "uuid",
  "agent": "evaluator",
  "model": "claude-opus-4-20250514",
  "iteration": 2,
  "latency_ms": 1234,
  "verdict": "fail",
  "score": 0.61
}
```

---

## 10. Authentication

Authentication is username/password with JWT sessions. Users are hardcoded in
the environment variable `AUTH_USERS`. This is intentionally simple for the
initial version — SSO/OAuth integration is a future milestone.

### Hardcoded Users (default)
```
admin  / admin123   → roles: ["admin", "developer"]
dev    / dev123     → roles: ["developer"]
```

### Login Flow
```
POST /api/v1/auth/login
Body: { "username": "admin", "password": "admin123" }

Response:
{
  "access_token": "eyJ...",
  "token_type": "bearer",
  "expires_in": 28800,
  "user": { "username": "admin", "roles": ["admin", "developer"] }
}
```

### JWT Payload
```json
{
  "sub": "admin",
  "roles": ["admin", "developer"],
  "exp": 1704067200,
  "iat": 1704038400
}
```

### Route Protection
- `/api/v1/chat/*` — requires any valid JWT
- `/api/v1/feedback/*` — requires any valid JWT
- `/api/v1/audit/*` — requires `admin` role
- `/api/v1/auth/*` — public

---

## 11. UI/UX Specification

### Design Language
- **Style:** Professional, clean, dark-mode-first
- **Font:** Inter (system font stack)
- **Primary colour:** Indigo (#6366f1) with slate neutrals
- **Component library:** shadcn/ui (Radix UI primitives + Tailwind)
- **Icons:** Lucide React

### Pages

#### Login Page (`/login`)
- Centred card with DigitalArchitect logo/wordmark
- Username and password fields
- "Sign In" button with loading state
- Error banner for invalid credentials
- No "forgot password" (hardcoded auth)

#### Chat Page (`/chat`) — primary interface
Layout: fixed sidebar (left, 260px) + main chat area + optional detail panel

**Sidebar:**
- DigitalArchitect logo + "Developer Knowledge Assistant" tagline
- "New Conversation" button
- Conversation history list (recent 20)
- Bottom: logged-in user badge + logout

**Chat Area:**
- Welcome state (empty): domain cards showing BE/FE/DB/Infra with example questions
- Message thread: user messages (right-aligned, indigo) + assistant messages (left, slate card)
- Each assistant message shows:
  - Domain badge(s): coloured pill (BE=blue, FE=green, DB=orange, Infra=purple)
  - Source documents collapsed/expandable
  - Evaluation score (optional tooltip showing dimension breakdown)
  - Feedback widget: three buttons — 👎 Below / 👍 Meets / ⭐ Exceeds
- Input bar (bottom, fixed): textarea + Send button + domain hint
- Thinking indicator: animated "Analysing query → Routing to BE specialist → Evaluating..." steps

**Escalation Banner:**
When a conversation is escalated, show a non-dismissible amber banner:
```
⚠ This question has been escalated to the Architecture Team (Ticket: AQ-12345).
  You'll receive a notification here when they respond.
```

#### Audit Dashboard (`/audit`) — admin only
- Summary cards: total queries today, avg eval score, escalation rate, top domain
- Evaluation score trends (line chart over time)
- Conversation table: query | domains | score | feedback | status | timestamp
- Model performance comparison table
- User feedback distribution (donut chart)
- Escalation log with resolution status

### Thinking Indicator Component
Shows real-time pipeline progress as SSE events stream from the backend:
```
● Classifying domain...          ✓ Backend + Database
● Retrieving BE context...       ✓ 5 chunks retrieved
● Retrieving DB context...       ✓ 5 chunks retrieved
● Merging specialist drafts...   ✓ Merged
● Evaluating response...         ✓ Score: 0.87 — Pass
```

---

## 12. Email Integration

### Provider: SendGrid
**Package:** `sendgrid` Python SDK

### Email Agent → SendGrid Flow
```python
# backend/tools/email_tool.py
import sendgrid
from sendgrid.helpers.mail import Mail

async def send_escalation_email(content: EmailContent, recipient: str) -> str:
    sg = sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)
    message = Mail(
        from_email=(settings.email_from, settings.email_from_name),
        to_emails=recipient,
        subject=content.subject,
        html_content=content.body_html,
        plain_text_content=content.body_text,
    )
    response = sg.client.mail.send.post(request_body=message.get())
    message_id = response.headers.get("X-Message-Id", "")
    return message_id
```

### Expert Reply Re-entry
When the architect team replies to the escalation email, their reply is handled by:
1. **MVP:** Admin pastes the expert answer via a UI form at `/audit/escalations/{ticket_id}/resolve`
2. **Production:** SendGrid Inbound Parse webhook → `POST /api/v1/webhook/email-reply`

On resolution:
1. Update `EscalationRecord.expert_reply` and `resolved_at`
2. Update `Conversation.status = "completed"` and `expert_answer`
3. Notify the original developer in the chat UI (if session is active)
4. Ingest the expert answer into ChromaDB (optional, admin-triggered)

### Recipient Configuration
Default: `settings.architect_team_email = "architecture-team@example.com"`
Configurable via env var `ARCHITECT_TEAM_EMAIL`.

---

## 13. Vector Database

### ChromaDB Setup
```python
# backend/vector/chroma_client.py
import chromadb
from chromadb.config import Settings

def get_chroma_client():
    return chromadb.PersistentClient(
        path=settings.chroma_persist_dir,
        settings=Settings(anonymized_telemetry=False)
    )

def get_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=settings.chroma_collection_name,
        metadata={"hnsw:space": "cosine"}
    )
```

### Document Ingestion (`scripts/ingest_docs.py`)
```
Chunking strategy:
- Split each markdown document by H2 headings (## sections)
- Minimum chunk size: 200 characters
- Maximum chunk size: 1500 characters
- Overlap: 100 characters between chunks

Metadata per chunk:
{
  "filename": "java_springboot_security_jwt.md",
  "domain": "BE",
  "stack": "Java+SpringBoot",
  "section": "JWT Security Framework — Spring Boot",
  "chunk_index": 0
}
```

### Retrieval with Domain Filter
```python
results = collection.query(
    query_texts=[rewritten_query],
    n_results=settings.chroma_top_k,
    where={"domain": {"$eq": domain}},
    include=["documents", "metadatas", "distances", "ids"]
)
```

---

## 14. Evaluation & Feedback

### Model Evaluation (Automated)
Performed by EvaluatorAgent after every specialist/merge response.
Scores (0–1) on five dimensions stored in `evaluation_records` table:
- **Groundedness** (weight 0.35) — most important: is it grounded in retrieved context?
- **Relevance** (weight 0.25) — does it answer the actual question?
- **Completeness** (weight 0.20) — does it cover all aspects?
- **Accuracy** (weight 0.15) — is the technical content correct?
- **Clarity** (weight 0.05) — is it well-written and actionable?

Pass threshold: `overall_score >= settings.eval_pass_threshold` (default 0.75)

### User Feedback (Manual)
Displayed after every assistant response. Three options:

| Rating | Value stored | Meaning |
|--------|-------------|---------|
| 👎 Below Expectations | `below_expectations` | Answer was wrong, incomplete, or unhelpful |
| 👍 Meets Expectations | `meets_expectations` | Answer was correct and useful |
| ⭐ Exceeds Expectations | `exceeds_expectations` | Answer was exceptional — saved significant time |

Feedback is optional. Users can also add a free-text comment.
Stored in `user_feedback` table linked to `conversation_id`.

### Feedback → Improvement Loop
- Weekly review: admin reviews conversations where user feedback = "below_expectations" but eval score was high → indicates evaluator calibration issue
- Escalation review: admin reviews resolved escalations → triggers KB ingestion for expert answers

---

## 15. Implementation Checklist

### Phase 1 — Core Pipeline
- [ ] FastAPI app factory with lifespan, middleware, CORS
- [ ] JWT auth with hardcoded users
- [ ] ChromaDB client + document ingestion script
- [ ] OrchestratorAgent with domain classification
- [ ] 4 specialist agents (BE, FE, DB, Infra) with retrieval_tool
- [ ] EvaluatorAgent with 5-dimension scoring
- [ ] SQLite audit DB + all table models
- [ ] AuditService recording every agent execution
- [ ] `POST /api/v1/chat` endpoint (synchronous first, SSE later)

### Phase 2 — Advanced Agents
- [ ] MergeAgent + merge_tool for multi-domain queries
- [ ] Fan-out with `asyncio.gather` in orchestrator
- [ ] EmailAgent + SendGrid email_tool
- [ ] Escalation flow + ConversationState persistence
- [ ] SSE endpoint for real-time thinking indicator

### Phase 3 — Frontend
- [ ] Next.js app with Tailwind + shadcn/ui
- [ ] Login page + JWT session management
- [ ] Chat page: message thread, domain badges, thinking indicator
- [ ] Feedback widget (Below/Meets/Exceeds)
- [ ] Escalation banner
- [ ] Audit dashboard (admin only)

### Phase 4 — Expert Reply Loop
- [ ] Admin UI for resolving escalations
- [ ] Expert answer → developer notification
- [ ] Optional: KB ingestion from expert answers
- [ ] Optional: SendGrid Inbound Parse webhook

---

*AGENTS.md version 1.0 — maintained by the Platform Architecture Team*
*Default escalation email: architecture-team@example.com*
