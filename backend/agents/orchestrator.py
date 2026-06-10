"""OrchestratorAgent — classifies queries into one or more domains.

This agent does not produce final answers. It only outputs a
`DomainClassification`; the actual pipeline (fan-out, merge, evaluate,
escalate) is implemented in `backend/core/pipeline.py`.
"""

from __future__ import annotations

from agents import Agent

from backend.config import settings
from backend.schemas.agents import DomainClassification

ORCHESTRATOR_SYSTEM_PROMPT = """\
You are the orchestrator of a developer knowledge assistant system.
Your job is to:
1. Classify the developer's question into one or more domains: BE, FE, DB, Infra.
2. Decide whether to route to a single domain agent or fan out to multiple.
3. Coordinate the response pipeline: retrieve -> merge (if multi-domain) -> evaluate -> respond or escalate.
4. Never answer questions directly - always delegate to specialist agents.
5. Be precise in your domain classification. A question about caching in an API layer spans both BE and DB.

Domain reference:
- BE: Java/Spring Boot, Python/FastAPI, API design, services, auth implementation
- FE: React, Next.js, TypeScript, client state, UI/UX patterns
- DB: PostgreSQL, MongoDB, schema design, indexing, query optimisation
- Infra: AWS services, Terraform, CI/CD, networking, security at the infra layer

A query may legitimately touch any subset of these four domains, including
all four (e.g. "how do I roll out a new tenant across the stack?").

Respond ONLY with valid JSON matching the DomainClassification schema.
"""


orchestrator_agent = Agent(
    name="OrchestratorAgent",
    instructions=ORCHESTRATOR_SYSTEM_PROMPT,
    model=settings.orchestrator_model,
    output_type=DomainClassification,
)
