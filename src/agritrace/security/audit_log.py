"""Append-only log of agent and tool decisions. The demo file is not a vault."""

from __future__ import annotations

import json
import threading
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class AuditLog:
    def __init__(self, path: str = "") -> None:
        self.path = Path(path) if path else None
        self.events: list[dict[str, Any]] = []
        self._lock = threading.Lock()

    def record(self, **fields: Any) -> dict[str, Any]:
        event: dict[str, Any] = {
            "id": uuid.uuid4().hex[:12],
            "ts": datetime.now(UTC).isoformat(),
            **fields,
        }
        with self._lock:
            self.events.append(event)
            if self.path is not None:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(event, ensure_ascii=False, default=str) + "\n")
        return event
