#!/usr/bin/env python3
"""
Generate Xentic framework documentation via LLM.

Phased generation:
  --phase 1  Regenerate 48 existing topics (seeded from archive/)
  --phase 2  Generate 52 new topics
  --phase all  Both phases

Usage (from project root):
  uv run python scripts/generate_framework_docs.py --phase 1
  uv run python scripts/generate_framework_docs.py --phase 2 --limit 5
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import LOGS_DIR  # noqa: E402

OUTPUT_DIR = PROJECT_ROOT / "data" / "framework_docs"
ARCHIVE_DIR = PROJECT_ROOT / "archive" / "framework_docs"
TOPICS_PHASE2 = Path(__file__).resolve().parent / "topics" / "phase2_new.json"
ARCHIVE_MANIFEST = ARCHIVE_DIR / "manifest.json"

MIN_LINES = 500
DEFAULT_MODEL = os.getenv("FRAMEWORK_DOC_MODEL", "gpt-4o-mini")
MAX_RETRIES = 3

SYSTEM_PROMPT = """You are a senior architect at Xentic writing internal engineering standards documents.

Organization rules (mandatory):
- Company: Xentic
- Java base packages: com.xentic.<service> (never com.company)
- Shared libraries: com.xentic.auth:auth-starter, com.xentic.common:*, etc.
- Use realistic fictional internal URLs (e.g. https://docs.internal.xentic.io)
- Prescriptive tone: MUST, SHOULD, MUST NOT
- Include concrete config (YAML, HCL, properties), SQL, and code examples appropriate to the stack
- Output ONLY markdown body content for the requested section (no JSON, no meta-commentary)
"""

DOC_PARTS: list[tuple[str, str, int]] = [
    (
        "## Overview and scope",
        "Purpose, audience, scope, non-goals, glossary, and how this standard fits the Xentic platform.",
        52,
    ),
    (
        "## Standards and policies",
        "Numbered MUST/SHOULD/MUST NOT policies. Reference com.xentic conventions where relevant.",
        52,
    ),
    (
        "## Architecture and design",
        "Component diagram description (mermaid block), data flows, integration points, failure domains.",
        52,
    ),
    (
        "## Configuration reference",
        "application.yml / Terraform / env vars tables with defaults and production values.",
        52,
    ),
    (
        "## Implementation guide",
        "Step-by-step implementation with full code examples (multiple classes/modules).",
        52,
    ),
    (
        "## Security requirements",
        "Threat model summary, authn/z, secrets, input validation, audit logging.",
        52,
    ),
    (
        "## Testing strategy",
        "Unit, integration, contract tests; coverage targets; example test classes.",
        52,
    ),
    (
        "## Observability and operations",
        "Metrics, logs, traces, dashboards, alerts, SLOs, on-call runbook steps.",
        52,
    ),
    (
        "## Migration and versioning",
        "Upgrade paths, deprecation policy, backward compatibility, rollback.",
        52,
    ),
    (
        "## FAQ, anti-patterns, and checklists",
        "FAQ (10+ Q&A), anti-patterns table, pre-merge and production checklists.",
        52,
    ),
]


def load_phase1_topics() -> list[dict]:
    with open(ARCHIVE_MANIFEST, encoding="utf-8") as f:
        manifest = json.load(f)
    topics = []
    for entry in manifest:
        archive_path = ARCHIVE_DIR / entry["filename"]
        title = _title_from_archive(archive_path) or _title_from_filename(entry["filename"])
        topics.append(
            {
                "filename": entry["filename"],
                "domain": entry["domain"],
                "stack": entry["stack"],
                "title": title,
                "phase": 1,
            }
        )
    return topics


def load_phase2_topics() -> list[dict]:
    with open(TOPICS_PHASE2, encoding="utf-8") as f:
        return json.load(f)


def _title_from_archive(path: Path) -> str | None:
    if not path.exists():
        return None
    text = path.read_text(encoding="utf-8")
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return None


def _title_from_filename(filename: str) -> str:
    stem = filename.replace(".md", "")
    words = stem.replace("_", " ").split()
    return " ".join(w.capitalize() for w in words)


def output_path(topic: dict) -> Path:
    return OUTPUT_DIR / topic["domain"] / topic["filename"]


def line_count(text: str) -> int:
    return len(text.splitlines())


def load_seed(topic: dict) -> str:
    if topic.get("phase") != 1:
        return ""
    archive_path = ARCHIVE_DIR / topic["filename"]
    if not archive_path.exists():
        return ""
    seed = archive_path.read_text(encoding="utf-8")
    seed = seed.replace("com.company", "com.xentic")
    return seed[:4000]


def call_llm(
    client: OpenAI,
    model: str,
    topic: dict,
    heading: str,
    instructions: str,
    min_lines: int,
    document_so_far: str,
    seed: str,
) -> str:
    user_parts = [
        f"Document title (H1, write once only in first section): {topic['title']}",
        f"Domain: {topic['domain']} | Stack: {topic['stack']}",
        f"Write section: {heading}",
        f"Section instructions: {instructions}",
        f"Minimum lines for this section: {min_lines}",
        "Include code fences, tables, and bullet lists. Be exhaustive and enterprise-grade.",
    ]
    if seed:
        user_parts.append(
            "Expand and replace the following archived draft (migrate com.company → com.xentic):\n"
            f"```markdown\n{seed}\n```"
        )
    if document_so_far.strip():
        user_parts.append(
            "Document written so far (do not repeat; continue consistently):\n"
            f"```markdown\n{document_so_far[-8000:]}\n```"
        )
    if heading != "## Overview and scope":
        user_parts.append("Do NOT repeat the H1 title line.")

    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "\n\n".join(user_parts)},
        ],
        temperature=0.4,
        max_tokens=4096,
    )
    content = (response.choices[0].message.content or "").strip()
    content = re.sub(r"^```markdown\s*", "", content)
    content = re.sub(r"\s*```$", "", content)
    return content.strip()


def expand_document(
    client: OpenAI,
    model: str,
    topic: dict,
    content: str,
    target_lines: int,
) -> str:
    deficit = target_lines - line_count(content)
    user = (
        f"The following Xentic standards document for '{topic['title']}' has {line_count(content)} lines "
        f"but requires at least {target_lines}.\n"
        f"Add approximately {deficit + 20} new lines by deepening existing sections "
        "(more examples, runbooks, tables, FAQ entries). "
        "Do not remove content. Return the FULL updated markdown document.\n\n"
        f"```markdown\n{content}\n```"
    )
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user},
        ],
        temperature=0.3,
        max_tokens=16384,
    )
    expanded = (response.choices[0].message.content or "").strip()
    expanded = re.sub(r"^```markdown\s*", "", expanded)
    expanded = re.sub(r"\s*```$", "", expanded)
    return expanded.strip() or content


def generate_document(client: OpenAI, model: str, topic: dict) -> str:
    seed = load_seed(topic)
    parts: list[str] = []
    document = ""

    for i, (heading, instructions, min_lines) in enumerate(DOC_PARTS):
        print(f"    section {i + 1}/{len(DOC_PARTS)}: {heading}")
        section_text = ""
        for attempt in range(MAX_RETRIES):
            try:
                section_text = call_llm(
                    client,
                    model,
                    topic,
                    heading,
                    instructions,
                    min_lines,
                    document,
                    seed if i == 0 else "",
                )
                if line_count(section_text) >= min_lines - 10:
                    break
                print(f"      retry {attempt + 1}: section too short ({line_count(section_text)} lines)")
            except Exception as exc:
                print(f"      error: {exc}")
                if attempt == MAX_RETRIES - 1:
                    raise
                time.sleep(2**attempt)

        if i == 0 and not section_text.lstrip().startswith("# "):
            section_text = f"# {topic['title']}\n\n{section_text}"
        parts.append(section_text)
        document = "\n\n".join(parts)

    for attempt in range(MAX_RETRIES):
        if line_count(document) >= MIN_LINES:
            break
        print(f"    expand pass {attempt + 1}: {line_count(document)} lines < {MIN_LINES}")
        document = expand_document(client, model, topic, document, MIN_LINES)

    return document


def write_manifest(topics: list[dict]) -> None:
    manifest = []
    for topic in sorted(topics, key=lambda t: (t["domain"], t["filename"])):
        rel = f"{topic['domain']}/{topic['filename']}"
        path = OUTPUT_DIR / topic["domain"] / topic["filename"]
        if path.exists() and line_count(path.read_text(encoding="utf-8")) >= MIN_LINES:
            manifest.append(
                {
                    "filename": rel,
                    "domain": topic["domain"],
                    "stack": topic["stack"],
                    "title": topic["title"],
                    "phase": topic.get("phase", 1),
                    "lines": line_count(path.read_text(encoding="utf-8")),
                }
            )
    with open(OUTPUT_DIR / "manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    print(f"\nManifest: {len(manifest)} documents -> {OUTPUT_DIR / 'manifest.json'}")


def ensure_dirs() -> None:
    for domain in ("BE", "FE", "DB", "Infra"):
        (OUTPUT_DIR / domain).mkdir(parents=True, exist_ok=True)


class _Tee:
    """Write to multiple streams (e.g. console and a log file)."""

    def __init__(self, *streams) -> None:
        self._streams = streams

    def write(self, data: str) -> None:
        for stream in self._streams:
            stream.write(data)
            stream.flush()

    def flush(self) -> None:
        for stream in self._streams:
            stream.flush()


def configure_run_logging(phase: str) -> Path:
    """Mirror stdout/stderr to ``logs/generation_phase{phase}.log``."""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    log_path = LOGS_DIR / f"generation_phase{phase}.log"
    log_file = log_path.open("a", encoding="utf-8")
    sys.stdout = _Tee(sys.__stdout__, log_file)
    sys.stderr = _Tee(sys.__stderr__, log_file)
    return log_path


def select_topics(phase: str) -> list[dict]:
    if phase == "1":
        return load_phase1_topics()
    if phase == "2":
        return load_phase2_topics()
    return load_phase1_topics() + load_phase2_topics()


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate Xentic framework docs via LLM")
    parser.add_argument("--phase", choices=["1", "2", "all"], default="all")
    parser.add_argument("--limit", type=int, default=0, help="Max documents to generate (0 = all)")
    parser.add_argument("--force", action="store_true", help="Regenerate even if file meets MIN_LINES")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--manifest-only", action="store_true", help="Rebuild manifest from disk")
    args = parser.parse_args()

    load_dotenv(PROJECT_ROOT / ".env", override=True)
    log_path = configure_run_logging(args.phase)
    print(f"Logging to {log_path}")
    ensure_dirs()

    if args.phase == "1":
        topics = load_phase1_topics()
    elif args.phase == "2":
        topics = load_phase2_topics()
    else:
        topics = load_phase1_topics() + load_phase2_topics()

    if args.limit > 0:
        topics = topics[: args.limit]

    if args.manifest_only:
        all_topics = load_phase1_topics() + load_phase2_topics()
        write_manifest(all_topics)
        return 0

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("ERROR: OPENAI_API_KEY not set. Add it to .env or environment.", file=sys.stderr)
        return 1

    client = OpenAI(api_key=api_key)
    generated = 0
    skipped = 0
    failed = 0

    print(f"Model: {args.model} | Min lines: {MIN_LINES} | Topics: {len(topics)}")

    for idx, topic in enumerate(topics, start=1):
        path = output_path(topic)
        rel = f"{topic['domain']}/{topic['filename']}"
        print(f"\n[{idx}/{len(topics)}] {rel}")

        if path.exists() and not args.force:
            existing_lines = line_count(path.read_text(encoding="utf-8"))
            if existing_lines >= MIN_LINES:
                print(f"  skip ({existing_lines} lines)")
                skipped += 1
                continue

        try:
            content = generate_document(client, args.model, topic)
            lines = line_count(content)
            if lines < MIN_LINES:
                print(f"  WARNING: {lines} lines < {MIN_LINES} after expansion")
            path.write_text(content + "\n", encoding="utf-8")
            print(f"  wrote {lines} lines -> {path}")
            generated += 1
        except Exception as exc:
            print(f"  FAILED: {exc}")
            failed += 1

        time.sleep(0.5)

    all_topics = load_phase1_topics() + load_phase2_topics()
    write_manifest(all_topics)

    print(f"\nDone: generated={generated} skipped={skipped} failed={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
