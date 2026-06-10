"""Watch framework_docs for changes and trigger versioned re-ingestion.

Usage:
  uv run python scripts/watch_docs.py

For CI, call POST /api/v1/documents/ingest/watch instead.
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

try:
    from watchfiles import Change, awatch
except ImportError:
    print("Install watchfiles: uv pip install watchfiles")
    raise


async def _run_watch() -> None:
    from backend.db.session import init_db
    from backend.vector.doc_identity import FRAMEWORK_DOCS_DIR
    from backend.vector.versioned_ingest import ingest_file

    await init_db()
    print(f"Watching {FRAMEWORK_DOCS_DIR} for markdown changes...")
    async for changes in awatch(FRAMEWORK_DOCS_DIR):
        for change, path in changes:
            p = Path(path)
            if p.suffix.lower() != ".md":
                continue
            if change == Change.deleted:
                from backend.db import document_service
                from backend.vector.versioned_ingest import deprecate_document

                try:
                    rel = str(p.relative_to(FRAMEWORK_DOCS_DIR)).replace("\\", "/")
                except ValueError:
                    continue
                doc = await document_service.get_document_by_path(rel)
                if doc:
                    result = await deprecate_document(
                        doc.doc_id,
                        ingested_by="watcher",
                        change_summary="File deleted",
                    )
                    print(f"deprecated {result.doc_id}")
                continue
            result = await ingest_file(p, ingested_by="watcher")
            print(f"{result.action} {result.doc_id} {result.version or ''} {result.message}")


def main() -> None:
    try:
        asyncio.run(_run_watch())
    except KeyboardInterrupt:
        print("Watcher stopped.")


if __name__ == "__main__":
    main()
