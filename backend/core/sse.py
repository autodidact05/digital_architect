"""Server-Sent-Events plumbing for the chat thinking indicator.

The pipeline pushes progress events into a per-conversation `asyncio.Queue`.
The SSE endpoint drains that queue and forwards each event to the client as
a JSON-encoded SSE message until the terminal `done` event is observed.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any


@dataclass
class PipelineEvent:
    stage: str
    status: str  # "started" | "completed" | "info" | "error"
    detail: dict[str, Any]

    def to_sse(self) -> dict[str, str]:
        payload = {"stage": self.stage, "status": self.status, **self.detail}
        return {"event": "pipeline", "data": json.dumps(payload)}


class PipelineEmitter:
    """A pipeline emitter is either a real SSE queue or a no-op sink.

    The synchronous `/chat` endpoint uses the no-op sink; the streaming
    `/chat/stream/{id}` endpoint owns the queue and forwards every event.
    """

    def __init__(self, queue: "asyncio.Queue[PipelineEvent | None] | None" = None):
        self._queue = queue

    async def emit(self, stage: str, status: str, **detail: Any) -> None:
        if self._queue is None:
            return
        await self._queue.put(PipelineEvent(stage=stage, status=status, detail=detail))

    async def close(self) -> None:
        if self._queue is not None:
            await self._queue.put(None)
