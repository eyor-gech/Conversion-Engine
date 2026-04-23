from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any, Literal

import httpx

from core.cache import get_cache
from core.rate_limiter import get_guards

TaskType = Literal["eval", "reasoning", "classification", "summarization"]


def _read_dotenv_value(key: str) -> str | None:
    env_path = Path(__file__).resolve().parents[1] / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        if not line or line.lstrip().startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        if k.strip() == key:
            return v.strip().strip('"').strip("'")
    return None


class OpenRouterClient:
    def __init__(self, timeout_s: float = 30.0) -> None:
        self.timeout_s = timeout_s
        self.api_key = os.getenv("OPENROUTER_API_KEY") or _read_dotenv_value("OPENROUTER_API_KEY") or ""
        self.mock_mode = os.getenv("MOCK_MODE", "true").lower() == "true"
        self.models: dict[str, str] = {
            "eval": "openai/gpt-4o-mini",
            "reasoning": "gemini/gemini-2.5-flash",
            "classification": "openai/gpt-4o-mini",
            "summarization": "google/gemini-2.0-flash-lite",
        }
 
    def model_for(self, task_type: TaskType) -> str:
        return self.models[task_type]

    async def complete(
        self,
        *,
        task_type: TaskType,
        prompt: str,
        function_name: str,
        max_retries: int = 4,
    ) -> dict[str, Any]:
        model = self.model_for(task_type)
        cache = get_cache()
        key = cache.make_key(function_name=function_name, model=model, payload={"task_type": task_type, "prompt": prompt})
        cached = cache.get(key)
        if cached is not None:
            return cached

        if self.mock_mode or not self.api_key:
            response = {
                "model": model,
                "task_type": task_type,
                "text": f"[MOCK:{task_type}] {prompt[:180]}",
                "cached": False,
            }
            cache.set(key, response)
            return response

        body = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.0,
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        guards = get_guards()
        delay = 0.5
        async with guards.llm_slot(provider="openrouter"):
            for attempt in range(max_retries + 1):
                try:
                    async with httpx.AsyncClient(timeout=self.timeout_s) as client:
                        resp = await client.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=body)
                    if resp.status_code == 429:
                        if attempt == max_retries:
                            break
                        await asyncio.sleep(delay)
                        delay *= 2
                        continue
                    resp.raise_for_status()
                    parsed = resp.json()
                    text = parsed["choices"][0]["message"]["content"]
                    response = {"model": model, "task_type": task_type, "text": text, "raw": parsed}
                    cache.set(key, response)
                    return response
                except (httpx.TimeoutException, httpx.HTTPStatusError, httpx.TransportError):
                    if attempt == max_retries:
                        break
                    await asyncio.sleep(delay)
                    delay *= 2

        fallback = {"model": model, "task_type": task_type, "text": "[FALLBACK] rate-limited/unavailable", "cached": False}
        cache.set(key, fallback)
        return fallback


_CLIENT: OpenRouterClient | None = None


def get_openrouter_client() -> OpenRouterClient:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = OpenRouterClient()
    return _CLIENT

