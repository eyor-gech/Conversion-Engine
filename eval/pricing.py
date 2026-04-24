from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ModelPricing:
    prompt_per_1k: float
    completion_per_1k: float


PRICING_USD_PER_1K: dict[str, ModelPricing] = {
    # Conservative explicit assumptions for synthetic accounting.
    "openai/gpt-4o-mini": ModelPricing(prompt_per_1k=0.00015, completion_per_1k=0.0006),
    "openai/gpt-5": ModelPricing(prompt_per_1k=0.00125, completion_per_1k=0.005),
    "gemini/gemini-2.5-flash": ModelPricing(prompt_per_1k=0.0003, completion_per_1k=0.0012),
    "google/gemini-2.0-flash-lite": ModelPricing(prompt_per_1k=0.000075, completion_per_1k=0.0003),
}


def estimate_cost_usd(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    pricing = PRICING_USD_PER_1K.get(model, PRICING_USD_PER_1K["openai/gpt-4o-mini"])
    prompt_cost = (prompt_tokens / 1000.0) * pricing.prompt_per_1k
    completion_cost = (completion_tokens / 1000.0) * pricing.completion_per_1k
    return round(prompt_cost + completion_cost, 8)

