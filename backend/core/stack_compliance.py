"""Approved technology stack policy (orchestrator guard + deterministic hints)."""

from __future__ import annotations

import re

from backend.schemas.agents import DomainClassification

# Human-readable list (matches org policy; keep in sync with orchestrator prompt).
APPROVED_STACKS_LINE = (
    "Java/Spring Boot, Python/FastAPI, React, Next.js, Kafka, Elasticsearch, "
    "PostgreSQL, MongoDB, and AWS (plus Terraform / GitHub Actions where "
    "documented for those stacks)."
)

# (regex, display name) — word-boundary style patterns; deterministic override
# when the model misses an out-of-scope technology.
_OUT_OF_SCOPE_SIGNALS: tuple[tuple[str, str], ...] = (
    (r"\brust\b", "Rust"),
    (r"\bcargo\.toml\b", "Rust (Cargo)"),
    (r"\bactix\b", "Rust (Actix)"),
    (r"\baxum\b", "Rust (Axum)"),
    (r"\bgolang\b", "Go"),
    (r"\bbun\b", "Bun"),
    (r"\belixir\b", "Elixir"),
    (r"\berlang\b", "Erlang"),
    (r"\bphoenix\b", "Phoenix"),
    (r"\bruby on rails\b", "Ruby on Rails"),
    (r"\brails\b", "Ruby on Rails"),
    (r"\bphp\b", "PHP"),
    (r"\blaravel\b", "Laravel"),
    (r"\bdjango\b", "Django"),
    (r"\bflask\b", "Flask"),
    (r"\bdeno\b", "Deno"),
    (r"\b\.net\b", ".NET"),
    (r"\bc#\b", "C#"),
    (r"\bf#\b", "F#"),
    (r"\bkotlin\b", "Kotlin"),
    (r"\bswift\b", "Swift"),
    (r"\bdart\b", "Dart"),
    (r"\bflutter\b", "Flutter"),
    (r"\bsvelte\b", "Svelte"),
    (r"\bvue\.?js\b", "Vue"),
    (r"\bnuxt\b", "Nuxt"),
    (r"\bangular\b", "Angular"),
)


def _deterministic_out_of_scope_technologies(query: str) -> list[str]:
    text = query.lower()
    found: list[str] = []
    seen: set[str] = set()
    for pattern, label in _OUT_OF_SCOPE_SIGNALS:
        if re.search(pattern, text, re.IGNORECASE):
            if label not in seen:
                seen.add(label)
                found.append(label)
    return found


def default_refusal_markdown(detected: list[str]) -> str:
    tech = ", ".join(detected) if detected else "the requested technology"
    return (
        "## Outside approved stack\n\n"
        f"This assistant only answers questions aligned with our **approved "
        f"technology stack**: {APPROVED_STACKS_LINE}\n\n"
        f"Your question appears to focus on **{tech}**, which is **not** "
        "in that approved set, so we cannot run documentation-grounded "
        "answers for it here.\n\n"
        "**What we did:** the Architecture team has been notified by email "
        "with your question (see ticket below) so they can advise on "
        "exceptions or standards updates.\n\n"
        "If your work is actually on an approved stack (e.g. migrating to "
        "FastAPI or Spring Boot), rephrase with that context and we can "
        "help from the internal guides."
    )


def normalize_stack_compliance(
    classification: DomainClassification,
    query: str,
) -> DomainClassification:
    """Merge LLM output with deterministic overrides; set user-facing refusal text."""
    detected = _deterministic_out_of_scope_technologies(query)
    if detected:
        classification.within_approved_stack = False

    if classification.within_approved_stack:
        return classification

    # Blocked path: ensure refusal text is always present
    msg = (classification.out_of_stack_developer_message or "").strip()
    if not msg:
        classification.out_of_stack_developer_message = default_refusal_markdown(
            detected or ["an unapproved technology"],
        )
    else:
        # Prepend ticket hint if model returned plain text
        if "## " not in msg and "Architecture" not in msg:
            classification.out_of_stack_developer_message = (
                default_refusal_markdown(detected)
                + "\n\n---\n\n"
                + msg
            )

    if detected and not classification.policy_detected_technologies:
        classification.policy_detected_technologies = detected
    return classification
