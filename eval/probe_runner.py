from __future__ import annotations

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
