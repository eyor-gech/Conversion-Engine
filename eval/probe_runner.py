from __future__ import annotations

import asyncio
import json
import uuid
from pathlib import Path
from typing import Any

from agent.core.tracing import LangfuseTracer
from llm.reasoning_layer import get_reasoning_layer
from agent.core.state import ProbeResult


def run_probes(results: list[ProbeResult]) -> dict[str, object]:
    severity_count = {"low": 0, "medium": 0, "high": 0}
    for result in results:
        severity_count[result.severity.value] += 1
    return {
        "total": len(results),
        "severity_count": severity_count,
        "failures": [r for r in results if "failed" in r.observed_behavior.lower()],
    }


async def replay_probe_library(probe_path: Path, output_path: Path) -> dict[str, Any]:
    probes = json.loads(probe_path.read_text(encoding="utf-8"))
    tracer = LangfuseTracer(enabled=True, project="conversion-engine")
    reasoner = get_reasoning_layer()

    category_totals: dict[str, int] = {}
    category_triggers: dict[str, int] = {}
    executed: list[dict[str, Any]] = []

    for probe in probes:
        category = str(probe["category"])
        category_totals[category] = category_totals.get(category, 0) + 1
        trace_id = str(uuid.uuid4())
        scenario = str(probe["scenario"])
        llm = await reasoner.classify_email_reply(scenario)
        observed = llm.get("intent", "unknown")
        triggered = observed in {"unknown", "book_meeting"}  # deterministic trigger proxy
        if triggered:
            category_triggers[category] = category_triggers.get(category, 0) + 1

        row = {
            "trace_id": trace_id,
            "id": probe["id"],
            "category": category,
            "expected_failure": probe["expected_failure"],
            "observed_behavior": observed,
            "triggered": triggered,
        }
        tracer.log("probe_trace", row)
        executed.append(row)

    trigger_rate = {
        c: (category_triggers.get(c, 0) / category_totals[c]) for c in category_totals
    }
    result = {"total_probes": len(executed), "trigger_rate_by_category": trigger_rate, "traces": executed}
    output_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Replay probes and compute trigger rates")
    parser.add_argument("--probe-file", default="probes/probe_cases.json")
    parser.add_argument("--output-file", default="eval/probe_results.json")
    args = parser.parse_args()

    result = asyncio.run(replay_probe_library(Path(args.probe_file), Path(args.output_file)))
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
