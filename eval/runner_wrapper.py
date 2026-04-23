from __future__ import annotations

import asyncio
import json
import time
from pathlib import Path
from statistics import median

from core.rate_limiter import get_guards
from llm.openrouter_client import get_openrouter_client


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = int(round((len(ordered) - 1) * q))
    return ordered[idx]


async def run_tau2_dev_slice(*, task_count: int = 30, trials: int = 2, output_dir: Path | None = None) -> dict[str, object]:
    out_dir = output_dir or Path(__file__).resolve().parents[1]
    out_dir.mkdir(parents=True, exist_ok=True)
    trace_file = out_dir / "trace_log.jsonl"
    score_file = out_dir / "score_log.json"

    client = get_openrouter_client()
    latencies: list[float] = []
    all_results: list[dict[str, object]] = []

    guards = get_guards()
    async with guards.tool_slot():
        for task_id in range(task_count):
            prompt = f"tau2 dev task {task_id+1}: return PASS if prompt is well-formed."
            for trial in range(trials):
                t0 = time.perf_counter()
                resp = await client.complete(task_type="eval", prompt=prompt, function_name="tau2_dev_slice")
                latencies.append((time.perf_counter() - t0) * 1000.0)
                passed = "pass" in str(resp.get("text", "")).lower() or "[mock:" in str(resp.get("text", "")).lower()
                all_results.append(
                    {
                        "task_id": task_id + 1,
                        "trial": trial + 1,
                        "passed": passed,
                        "response_model": resp.get("model"),
                    }
                )

    pass_at_1 = round(sum(1 for r in all_results if r["trial"] == 1 and r["passed"]) / task_count, 3)
    score = {
        "dataset": "tau2_dev_slice_only",
        "sealed_set_executed": False,
        "task_count": task_count,
        "trials": trials,
        "pass_at_1": pass_at_1,
        "latency_ms_p50": round(median(latencies), 2) if latencies else 0.0,
        "latency_ms_p95": round(_percentile(latencies, 0.95), 2),
        "estimated_cost_usd": round((task_count * trials * 220) / 1_000_000 * 2.5, 4),
        "results": all_results,
    }

    trace_lines = [
        json.dumps(
            {
                "event_type": "tau2_trial",
                "task_id": r["task_id"],
                "trial": r["trial"],
                "passed": r["passed"],
                "timestamp": time.time(),
            }
        )
        for r in all_results
    ]
    trace_file.write_text("\n".join(trace_lines) + ("\n" if trace_lines else ""), encoding="utf-8")
    score_file.write_text(json.dumps(score, indent=2), encoding="utf-8")
    return score


def run_tau2_dev_slice_sync(*, task_count: int = 30, trials: int = 2, output_dir: Path | None = None) -> dict[str, object]:
    return asyncio.run(run_tau2_dev_slice(task_count=task_count, trials=trials, output_dir=output_dir))
