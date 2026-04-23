from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Any, Awaitable, Callable

EventHandler = Callable[[dict[str, Any]], Awaitable[None] | None]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def on(self, event_name: str, handler: EventHandler) -> None:
        self._handlers[event_name].append(handler)

    async def emit(self, event_name: str, payload: dict[str, Any]) -> None:
        for handler in self._handlers.get(event_name, []):
            outcome = handler(payload)
            if asyncio.iscoroutine(outcome):
                await outcome


_EMAIL_EVENT_BUS: EventBus | None = None
_SMS_EVENT_BUS: EventBus | None = None


def get_email_event_bus() -> EventBus:
    global _EMAIL_EVENT_BUS
    if _EMAIL_EVENT_BUS is None:
        _EMAIL_EVENT_BUS = EventBus()
    return _EMAIL_EVENT_BUS


def get_sms_event_bus() -> EventBus:
    global _SMS_EVENT_BUS
    if _SMS_EVENT_BUS is None:
        _SMS_EVENT_BUS = EventBus()
    return _SMS_EVENT_BUS

