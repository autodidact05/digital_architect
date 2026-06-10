"""Pydantic structured-output schemas for every agent.

These models are passed to `Agent(output_type=...)` so the OpenAI Agents SDK
forces each agent to emit JSON matching the contract defined in AGENTS.md §5.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Domain = Literal["BE", "FE", "DB", "Infra"]
Confidence = Literal["high", "medium", "low"]
Verdict = Literal["pass", "fail"]

# Manifest stack values (must match framework_docs/manifest.json).
StackName = Literal[
    "Java+SpringBoot",
    "Python+FastAPI",
    "React",
    "Next.js",
    "PostgreSQL",
    "MongoDB",
    "AWS",
]


class StackHintEntry(BaseModel):
    """Technology stack named by the developer for a given domain."""

    domain: Domain
    stack: StackName


class DomainClassification(BaseModel):
    """OrchestratorAgent output."""

    domains: list[Domain] = Field(
        description=(
            "One or more domains this question touches. May be any subset "
            "of {BE, FE, DB, Infra}, including all four."
        ),
        min_length=1,
    )
    is_multi_domain: bool = Field(
        description="True when len(domains) > 1."
    )
    reasoning: str = Field(
        description="Brief explanation of why these domains were chosen."
    )
    rewritten_query: str = Field(
        description=(
            "Cleaned, technical phrasing of the original question, suitable "
            "for downstream retrieval."
        )
    )
    needs_clarification: bool = Field(
        default=False,
        description=(
            "True when the question is too vague or ambiguous to route safely."
        ),
    )
    clarification_questions: list[str] = Field(
        default_factory=list,
        description=(
            "One to three specific questions for the developer when "
            "needs_clarification is true."
        ),
    )
    stack_hints: list[StackHintEntry] = Field(
        default_factory=list,
        description=(
            "When the developer names a technology, list entries with domain "
            "and stack, e.g. [{\"domain\": \"BE\", \"stack\": \"Java+SpringBoot\"}]."
        ),
    )
    within_approved_stack: bool = Field(
        default=True,
        description=(
            "False if the question is primarily about technologies OUTSIDE the "
            "org-approved stack (Java/Spring Boot, Python/FastAPI, React, Next.js, "
            "Kafka, Elasticsearch, PostgreSQL, MongoDB, AWS). Do not route to "
            "specialists when false."
        ),
    )
    out_of_stack_developer_message: str | None = Field(
        default=None,
        description=(
            "When within_approved_stack is false, a short polite Markdown message "
            "listing approved stacks and stating that documentation-based help "
            "is not available for the requested technology."
        ),
    )
    policy_detected_technologies: list[str] = Field(
        default_factory=list,
        description="Technologies the user asked about that triggered the policy gate.",
    )

    def stack_hint_for(self, domain: Domain) -> str | None:
        for entry in self.stack_hints:
            if entry.domain == domain:
                return entry.stack
        return None


class SpecialistDraft(BaseModel):
    """Shared output schema for every specialist agent."""

    domain: Domain
    answer: str = Field(description="The curated answer for this domain.")
    rewritten_query: str = Field(
        description="Domain-aware rewrite used for retrieval."
    )
    retrieved_chunk_ids: list[str] = Field(default_factory=list)
    answer_found: bool = Field(
        description="False when the retrieved context was insufficient."
    )
    confidence: Confidence
    sources: list[str] = Field(
        default_factory=list,
        description="Document filenames or titles referenced by this answer.",
    )


class MergedDraft(BaseModel):
    """MergeAgent output."""

    answer: str
    domains_covered: list[str]
    has_contradictions: bool
    contradiction_notes: str | None = None
    all_answer_found: bool
    sources: list[str] = Field(default_factory=list)
    retrieved_chunk_ids: list[str] = Field(default_factory=list)


class EvaluatorVerdict(BaseModel):
    """EvaluatorAgent output."""

    verdict: Verdict
    overall_score: float = Field(ge=0.0, le=1.0)
    groundedness: float = Field(ge=0.0, le=1.0)
    relevance: float = Field(ge=0.0, le=1.0)
    completeness: float = Field(ge=0.0, le=1.0)
    accuracy: float = Field(ge=0.0, le=1.0)
    clarity: float = Field(ge=0.0, le=1.0)
    feedback: str | None = Field(
        default=None,
        description="Populated on fail \u2014 specific improvement guidance.",
    )
    iteration: int = Field(ge=1)
    escalate: bool = Field(
        description="True when iteration == max and verdict == fail."
    )


class EmailContent(BaseModel):
    """EmailAgent output."""

    subject: str
    body_html: str
    body_text: str
    ticket_id: str
