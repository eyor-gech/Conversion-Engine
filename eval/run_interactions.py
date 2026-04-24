from __future__ import annotations

import argparse
import asyncio
import json
import time
from pathlib import Path
from statistics import median

from agent.orchestrator import run_single_synthetic_thread


def _pctl(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    idx = int(round((len(ordered) - 1) * q))
    return ordered[idx]


async def run_many(num_prospects: int, output_dir: Path) -> dict[str, object]:
    latencies: list[float] = []
    for _ in range(num_prospects):
        t0 = time.perf_counter()
        await run_single_synthetic_thread(output_dir=output_dir)
        latencies.append((time.perf_counter() - t0) * 1000.0)
    result = {
        "num_prospects": num_prospects,
        "end_to_end_latency_ms": {
            "p50": round(median(latencies), 3) if latencies else 0.0,
            "p95": round(_pctl(latencies, 0.95), 3),
        },
        "latencies_raw_ms": [round(v, 3) for v in latencies],
    }
    (output_dir / "interaction_metrics.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run synthetic interaction latency benchmark")
    parser.add_argument("--num-prospects", type=int, default=20)
    parser.add_argument("--output-dir", default="eval")
    args = parser.parse_args()
    out = Path(args.output_dir).resolve()
    out.mkdir(parents=True, exist_ok=True)
    result = asyncio.run(run_many(args.num_prospects, out))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

