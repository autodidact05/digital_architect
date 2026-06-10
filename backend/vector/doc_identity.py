"""Stable document identifiers and metadata from framework doc paths."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from pathlib import Path

from backend.config import FRAMEWORK_DOCS_DIR
MANIFEST_PATH = FRAMEWORK_DOCS_DIR / "manifest.json"

STACK_PREFIXES = (
    "java_springboot_",
    "python_fastapi_",
    "react_",
    "mongodb_",
    "postgresql_",
    "aws_",
)


@dataclass(frozen=True)
class DocumentFileMeta:
    doc_id: str
    relative_path: str
    domain: str
    stack: str
    title: str
    manifest_version: str | None


def sha256_text(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def slugify_doc_id(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return slug or "document"


def path_to_doc_id(relative_path: str) -> str:
    """e.g. BE/java_springboot_security.md -> be-java-springboot-security"""
    stem = Path(relative_path).stem
    domain_prefix = ""
    parts = relative_path.replace("\\", "/").split("/")
    if len(parts) >= 2:
        domain_prefix = parts[0].lower()
        return slugify_doc_id(f"{domain_prefix}-{stem}")
    return slugify_doc_id(stem)


def _derive_doc_type(filename: str) -> str:
    stem = Path(filename).stem
    for prefix in STACK_PREFIXES:
        if stem.startswith(prefix):
            return stem[len(prefix) :]
    return stem


def load_manifest() -> dict[str, dict]:
    if not MANIFEST_PATH.is_file():
        return {}
    with open(MANIFEST_PATH, encoding="utf-8") as f:
        entries = json.load(f)
    return {entry["filename"]: entry for entry in entries}


def resolve_file_meta(file_path: Path) -> DocumentFileMeta:
    """Resolve manifest + path metadata for a markdown file under framework_docs."""
    file_path = file_path.resolve()
    try:
        relative = str(file_path.relative_to(FRAMEWORK_DOCS_DIR)).replace("\\", "/")
    except ValueError as exc:
        raise ValueError(f"Path must be under {FRAMEWORK_DOCS_DIR}") from exc

    manifest = load_manifest()
    entry = manifest.get(relative, manifest.get(Path(relative).name, {}))

    doc_id = entry.get("doc_id") or path_to_doc_id(relative)
    domain = entry.get("domain") or (relative.split("/")[0] if "/" in relative else "BE")
    stack = entry.get("stack") or "unknown"
    title = entry.get("title") or Path(relative).stem.replace("_", " ")

    return DocumentFileMeta(
        doc_id=doc_id,
        relative_path=relative,
        domain=str(domain),
        stack=str(stack),
        title=str(title),
        manifest_version=entry.get("version"),
    )


def bump_patch_version(current: str) -> str:
    """Semantic patch bump: 2.1.0 -> 2.1.1"""
    parts = current.split(".")
    while len(parts) < 3:
        parts.append("0")
    try:
        parts[2] = str(int(parts[2]) + 1)
    except ValueError:
        return "1.0.0"
    return ".".join(parts[:3])


def next_version(
    current_version: str | None,
    *,
    manifest_version: str | None,
    content_changed: bool,
) -> str:
    if not content_changed:
        return current_version or manifest_version or "1.0.0"
    if manifest_version:
        return manifest_version
    if current_version:
        return bump_patch_version(current_version)
    return "1.0.0"
