from __future__ import annotations


def bench_safe(cost_usd: float, budget_cap_usd: float = 25.0) -> bool:
    return cost_usd <= budget_cap_usd
