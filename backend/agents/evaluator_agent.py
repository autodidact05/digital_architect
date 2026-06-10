"""EvaluatorAgent — quality-gates every response using a superior model."""

from __future__ import annotations

from agents import Agent

from backend.config import settings
from backend.schemas.agents import EvaluatorVerdict

EVALUATOR_SYSTEM_PROMPT = """\
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
- overall_score >= EVAL_PASS_THRESHOLD -> verdict: "pass"
- overall_score <  EVAL_PASS_THRESHOLD -> verdict: "fail"

The orchestrator will tell you the current iteration and the configured pass
threshold. On the final iteration with a failing verdict, set `escalate=true`.

If verdict is "fail", provide specific, actionable feedback that the specialist
agent can use to improve the answer in the next iteration.

Return ONLY valid JSON matching the EvaluatorVerdict schema.
"""


evaluator_agent = Agent(
    name="EvaluatorAgent",
    instructions=EVALUATOR_SYSTEM_PROMPT,
    model=settings.evaluator_model,
    output_type=EvaluatorVerdict,
)
