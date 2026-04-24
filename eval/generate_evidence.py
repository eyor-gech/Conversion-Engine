from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from eval.stats import bootstrap_difference_p_value


def _read_json(path: Path, default: Any) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    base = Path(__file__).resolve().parents[1]
    dev_score = _read_json(base / "eval" / "score_log.json", {})
    heldout_score = _read_json(base / "eval" / "heldout_summary.json", {})
    ablations = _read_json(base / "ablation_results.json", {})
    invoice = _read_json(base / "invoice_summary.json", {})

    baseline = [float(v) for v in dev_score.get("task_successes", [])]
    method = [float(v) for v in heldout_score.get("trial_successes", [])]
    stats = bootstrap_difference_p_value(baseline, method, n_resamples=10_000)

    evidence = {
        "metrics_to_evidence": {
            "dev_pass_at_1": {"value": dev_score.get("pass_at_1_mean"), "source_file": "eval/score_log.json"},
            "heldout_pass_at_1": {"value": heldout_score.get("pass_at_1"), "source_file": "eval/heldout_summary.json"},
            "ablation_confidence_aware": {"value": ablations.get("confidence_aware"), "source_file": "ablation_results.json"},
            "cost_per_task": {"value": invoice.get("estimated_cost_per_task_usd"), "source_file": "invoice_summary.json"},
            "delta_method_minus_baseline": {"value": stats["delta"], "source": "bootstrap_difference"},
            "p_value": {"value": stats["p_value"], "source": "bootstrap_difference"},
        },
        "stat_test": stats,
    }
    (base / "evidence_graph.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps(evidence, indent=2))


if __name__ == "__main__":
    main()
