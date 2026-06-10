"""Infer technology stack preferences from developer queries for retrieval."""

from __future__ import annotations

import re
from typing import Literal

Domain = Literal["BE", "FE", "DB", "Infra"]

# Manifest ``stack`` values used in Chroma metadata (see framework_docs/manifest.json).
BE_JAVA = "Java+SpringBoot"
BE_PYTHON = "Python+FastAPI"
FE_REACT = "React"
DB_POSTGRES = "PostgreSQL"
DB_MONGO = "MongoDB"
INFRA_AWS = "AWS"


def infer_stack_for_domain(query: str, domain: Domain) -> str | None:
    """Return a manifest stack string when the query names a technology explicitly."""
    q = query.lower()

    if domain == "BE":
        java_signals = (
            r"\bjava\b",
            r"\bspring\s*boot\b",
            r"\bspringboot\b",
            r"\bspring\b",
            r"\bjpa\b",
            r"\bflyway\b",
            r"\b@RestController\b".lower(),
        )
        python_signals = (
            r"\bfastapi\b",
            r"\bpydantic\b",
            r"\bsqlalchemy\b",
            r"\buvicorn\b",
        )
        java_hit = any(re.search(p, q) for p in java_signals)
        python_hit = any(re.search(p, q) for p in python_signals)
        if java_hit and not python_hit:
            return BE_JAVA
        if python_hit and not java_hit:
            return BE_PYTHON
        return None

    if domain == "FE":
        if re.search(r"\bnext\.?js\b", q) or re.search(r"\bnextjs\b", q):
            return "Next.js"
        if re.search(r"\breact\b", q) or re.search(r"\btypescript\b", q):
            return FE_REACT
        return None

    if domain == "DB":
        if re.search(r"\bpostgres", q) or re.search(r"\bpostgresql\b", q):
            return DB_POSTGRES
        if re.search(r"\bmongo", q):
            return DB_MONGO
        return None

    if domain == "Infra":
        if re.search(r"\baws\b", q) or re.search(r"\bterraform\b", q):
            return INFRA_AWS
        return None

    return None


def merge_stack_hint(
    *,
    query: str,
    domain: Domain,
    orchestrator_hint: str | None,
) -> str | None:
    """Prefer orchestrator hint, then heuristic inference from full query text."""
    if orchestrator_hint:
        return orchestrator_hint
    return infer_stack_for_domain(query, domain)
