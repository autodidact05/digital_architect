"""End-to-end smoke test against the live OpenAI + ChromaDB stack.

Runs three representative queries (single-domain BE, multi-domain BE+DB,
all-domain) and prints the resulting status, score, sources and ticket
(if escalated). Audit rows are also written, so this exercises the full
pipeline including persistence.

Usage::

    .venv/Scripts/python.exe scripts/smoke_pipeline.py [scenario]

Where `scenario` is one of: `be`, `multi`, `all`, `all-three`. Defaults to
`be` to minimise tokens.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Use widely available models for smoke tests unless the caller overrides.
os.environ.setdefault("EVALUATOR_MODEL", "gpt-4.1-mini")
os.environ.setdefault("MERGE_AGENT_MODEL", "gpt-4.1-mini")
os.environ.setdefault("ORCHESTRATOR_MODEL", "gpt-4.1-mini")

from dotenv import load_dotenv  # noqa: E402

load_dotenv(PROJECT_ROOT / ".env", override=False)

from backend.core.pipeline import run_pipeline  # noqa: E402
from backend.db.session import init_db  # noqa: E402
from backend.vector.chroma_client import warm_up as warm_vector_store  # noqa: E402

SCENARIOS = {
    "be": "Which signing algorithm must Spring Boot services use for JWTs?",
    "multi": (
        "How should I cache PostgreSQL query results from a Spring Boot service?"
    ),
    "all": (
        "We're rolling out a new tenant across React, FastAPI, PostgreSQL and "
        "AWS. What end-to-end patterns must I follow at every layer?"
    ),
    "all-three": (
        "How do we wire React forms through FastAPI down to MongoDB with "
        "ECS Fargate hosting?"
    ),
}


async def run(scenario: str) -> None:
    query = SCENARIOS.get(scenario)
    if query is None:
        raise SystemExit(
            f"Unknown scenario '{scenario}'. Choose one of: {', '.join(SCENARIOS)}"
        )

    await init_db()
    warm_vector_store()
    print(f"\n=== Scenario: {scenario} ===")
    print(f"Query: {query}\n")
    response = await run_pipeline(user_id="smoke-test", query=query)
    print(f"status      : {response.status}")
    print(f"domains     : {response.domains}")
    print(f"iterations  : {response.iterations}")
    if response.evaluation:
        ev = response.evaluation
        print(
            "evaluation  : "
            f"overall={ev.overall_score:.2f} verdict={ev.verdict} "
            f"groundedness={ev.groundedness:.2f} relevance={ev.relevance:.2f} "
            f"completeness={ev.completeness:.2f}"
        )
    if response.ticket_id:
        print(f"ticket_id   : {response.ticket_id}")
    print(f"sources     : {response.sources[:5]}")
    print("\n--- ANSWER ---\n")
    print(response.answer)


if __name__ == "__main__":
    scenario = sys.argv[1] if len(sys.argv) > 1 else "be"
    asyncio.run(run(scenario))
