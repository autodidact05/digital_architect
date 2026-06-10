"""Map framework document filenames to browsable URLs."""

from __future__ import annotations

from backend.config import settings
from backend.schemas.chat import SourceLink


def normalize_source_path(source: str) -> str:
    """Normalize a source string to a framework_docs-relative path."""
    path = source.replace("\\", "/").strip()
    if "framework_docs/" in path:
        path = path.split("framework_docs/", 1)[-1]
    return path.lstrip("/")


def build_source_link(source: str, title: str | None = None) -> SourceLink:
    rel = normalize_source_path(source)
    base = settings.framework_docs_base_url.rstrip("/")
    url = f"{base}/{rel}" if rel else base
    display = title or rel.split("/")[-1] or source
    return SourceLink(filename=rel or source, title=display, url=url)


def build_source_links(
    sources: list[str],
    *,
    version_by_source: dict[str, str] | None = None,
) -> list[SourceLink]:
    seen: set[str] = set()
    links: list[SourceLink] = []
    version_by_source = version_by_source or {}
    for src in sources:
        rel = normalize_source_path(src)
        if rel in seen:
            continue
        seen.add(rel)
        link = build_source_link(src)
        ver = version_by_source.get(rel) or version_by_source.get(src)
        links.append(
            SourceLink(
                filename=link.filename,
                title=link.title,
                url=link.url,
                doc_version=ver,
            )
        )
    return links


def version_map_from_retrieval(
  retrievals: list,
) -> dict[str, str]:
    """Map normalized source path -> doc_id:version label."""
    from backend.vector.chroma_client import RetrievalResult

    mapping: dict[str, str] = {}
    for result in retrievals:
        if not isinstance(result, RetrievalResult):
            continue
        for chunk in result.raw:
            if not chunk.source or not chunk.version_label:
                continue
            rel = normalize_source_path(chunk.source)
            mapping.setdefault(rel, chunk.version_label)
    return mapping
