"""Version-aware ingestion for all framework docs (replaces legacy full rebuild)."""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


async def _main() -> None:
    from backend.db.session import init_db
    from backend.vector.versioned_ingest import ingest_all_docs

    await init_db()
    results = await ingest_all_docs(ingested_by="cli:ingest_docs")
    ingested = sum(1 for r in results if r.action == "ingested")
    skipped = sum(1 for r in results if r.action == "skipped")
    print(f"Done. ingested={ingested} skipped={skipped} total={len(results)}")


def main() -> None:
    asyncio.run(_main())


if __name__ == "__main__":
    main()
