from __future__ import annotations

import asyncio
import os
from contextlib import asynccontextmanager
from typing import AsyncIterator


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, str(default)).strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return default


class ConcurrencyGuards:
    def __init__(self) -> None:
        self.max_llm = _env_int("MAX_LLM_CONCURRENCY", 2)
        self.max_tool = _env_int("MAX_TOOL_CONCURRENCY", 4)
        self._llm_sem = asyncio.Semaphore(self.max_llm)
        self._tool_sem = asyncio.Semaphore(self.max_tool)
        self._provider_locks: dict[str, asyncio.Semaphore] = {}
        self._provider_limit = max(1, min(2, self.max_llm))

    def _provider_sem(self, provider: str) -> asyncio.Semaphore:
        if provider not in self._provider_locks:
            self._provider_locks[provider] = asyncio.Semaphore(self._provider_limit)
        return self._provider_locks[provider]

    @asynccontextmanager
    async def llm_slot(self, provider: str = "openrouter") -> AsyncIterator[None]:
        provider_sem = self._provider_sem(provider)
        async with self._llm_sem:
            async with provider_sem:
                yield

    @asynccontextmanager
    async def tool_slot(self) -> AsyncIterator[None]:
        async with self._tool_sem:
            yield


_GLOBAL_GUARDS: ConcurrencyGuards | None = None


def get_guards() -> ConcurrencyGuards:
    global _GLOBAL_GUARDS
    if _GLOBAL_GUARDS is None:
        _GLOBAL_GUARDS = ConcurrencyGuards()
    return _GLOBAL_GUARDS

