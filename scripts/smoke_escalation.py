"""Force the escalation path by pushing EVAL_PASS_THRESHOLD to 1.01 and
MAX_EVAL_ITERATIONS to 1. The pipeline must produce a draft, fail the
evaluator, compose an escalation email, and persist an EscalationRecord.

Run::

    .venv/Scripts/python.exe scripts/smoke_escalation.py
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ["EVAL_PASS_THRESHOLD"] = "1.01"
os.environ["MAX_EVAL_ITERATIONS"] = "1"
os.environ.setdefault("EVALUATOR_MODEL", "gpt-4.1-mini")
os.environ.setdefault("MERGE_AGENT_MODEL", "gpt-4.1-mini")
os.environ.setdefault("ORCHESTRATOR_MODEL", "gpt-4.1-mini")

from dotenv import load_dotenv  # noqa: E402

load_dotenv(PROJECT_ROOT / ".env", override=False)

from backend.core.pipeline import run_pipeline  # noqa: E402
from backend.db.session import init_db  # noqa: E402
from backend.vector.chroma_client import warm_up as warm_vector_store  # noqa: E402


async def main() -> None:
    await init_db()
    warm_vector_store()
    response = await run_pipeline(
        user_id="smoke-test",
        query="Which signing algorithm must Spring Boot services use for JWTs?",
    )
    print(f"status     : {response.status}")
    print(f"ticket_id  : {response.ticket_id}")
    print(f"iterations : {response.iterations}")
    if response.evaluation:
        ev = response.evaluation
        print(
            f"evaluation : overall={ev.overall_score:.2f} verdict={ev.verdict}"
        )
    print("\n--- ANSWER (escalation message) ---\n")
    print(response.answer)


if __name__ == "__main__":
    asyncio.run(main())
