from __future__ import annotations

from agent.core.state import BenchResult
from eval.metrics import wilson_ci


def run_tau_bench(dev_scores: list[bool], held_out_scores: list[bool], avg_cost_usd: float) -> BenchResult:
    successes = sum(1 for s in held_out_scores if s)
    total = len(held_out_scores)
    pass_at_1 = successes / total if total else 0.0
    ci_low, ci_high = wilson_ci(successes, total)
    dataset_name = f"dev={len(dev_scores)}|held_out={len(held_out_scores)}"
    return BenchResult(
        dataset=dataset_name,
        pass_at_1=round(pass_at_1, 3),
        ci_low=round(ci_low, 3),
        ci_high=round(ci_high, 3),
        avg_cost_usd=round(avg_cost_usd, 4),
    )
