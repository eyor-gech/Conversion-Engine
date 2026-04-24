from __future__ import annotations

from typing import Any, Literal

from llm.openrouter_client import TaskType, get_openrouter_client


async def llm_complete(task_type: TaskType, prompt: str, function_name: str) -> dict[str, Any]:
    """
    Centralized LLM wrapper for the repository.
    Routes all calls through the OpenRouter client.
    """
    return await get_openrouter_client().complete(
        task_type=task_type,
        prompt=prompt,
        function_name=function_name,
    )

