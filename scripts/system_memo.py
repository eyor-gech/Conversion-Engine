from __future__ import annotations

import json
from pathlib import Path

from agent.core.orchestrator import run_sync
from eval.ablation import run_ablation


if __name__ == "__main__":
    report = run_sync("final")
    memo = {
        "mode": report.mode,
        "processed_companies": report.processed_companies,
        "pass_at_1": report.bench.pass_at_1,
        "ci": [report.bench.ci_low, report.bench.ci_high],
        "avg_cost_usd": report.bench.avg_cost_usd,
        "probe_count": len(report.probes),
        "ablation": [a.__dict__ for a in run_ablation()],
        "recommendation": "Proceed with guarded pilot using interim workflow and weekly probe review.",
    }
    out = Path(__file__).resolve().parents[1] / "system_memo.json"
    out.write_text(json.dumps(memo, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
