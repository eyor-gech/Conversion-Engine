from __future__ import annotations

import json

from agent.core.orchestrator import run_sync
from eval.ablation import run_ablation
from eval.failure_taxonomy import FAILURE_TAXONOMY
from eval.probe_runner import run_probes


if __name__ == "__main__":
    report = run_sync("final")
    probe_summary = run_probes(report.probes)
    out = {
        "report": report.model_dump(mode="json"),
        "probe_summary": {
            "total": probe_summary["total"],
            "severity_count": probe_summary["severity_count"],
            "failing_count": len(probe_summary["failures"]),
        },
        "ablation": [a.__dict__ for a in run_ablation()],
        "failure_taxonomy": FAILURE_TAXONOMY,
    }
    print(json.dumps(out, indent=2))
