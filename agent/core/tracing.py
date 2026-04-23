from __future__ import annotations

from datetime import datetime
from typing import Any


class LangfuseTracer:
    """Lightweight deterministic tracer that can be swapped for official SDK."""

    def __init__(self, enabled: bool = True, project: str = "conversion-engine") -> None:
        self.enabled = enabled
        self.project = project
        self.events: list[dict[str, Any]] = []

    def log(self, event_type: str, payload: dict[str, Any]) -> None:
        if not self.enabled:
            return
        try:
            self.events.append(
                {
                    "project": self.project,
                    "event_type": event_type,
                    "payload": payload,
                    "timestamp": datetime.utcnow().isoformat(),
                }
            )
        except Exception:
            # Observability failures must never block pipeline execution.
            return

    def export(self) -> list[dict[str, Any]]:
        return list(self.events)
