# Tenacious — Decision Memo

## Page 1: Executive Summary

**Baseline and held-out runs are reproducible** with trace-linked artifacts.
Confidence-aware phrasing outperformed binary/no-confidence ablations.
Recommended pilot: guarded rollout with weekly probe review.

### Key Metrics

| Metric | Value |
|---|---|
| tau2 dev baseline pass@1 | 0.5333 |
| held-out pass@1 | 0.87 |
| delta (held-out − dev) | 0.3367 |
| p-value (bootstrap, 10 000 resamples) | 0.0001 |
| confidence-aware ablation score | 0.76 |
| binary-threshold ablation score | 0.7 |
| no-confidence ablation score | 0.66 |
| cost per task (USD) | 0.000229 |

### Narrative

- **Stalled-thread delta:** modeled improvement via confidence conditioning (18 % of threads stall without it).
- **Reply-rate delta:** modeled positive lift vs. generic assertive phrasing.
- **Annualized impact:** conservative/base/aggressive scenarios embedded in `evidence_graph.json`.
- **Pilot recommendation:** proceed with guardrails enabled and kill-switch at > 3 % overclaim rate.

---

## Page 2: Risk & Traceability

### Failure Modes Not Covered by tau2

1. CRM identity split across aliases
2. Webhook schema drift on provider upgrade
3. Signal staleness from delayed data refresh
4. Tone-regression in retry-storm conditions

### Analysis

- **Signal lossiness:** jobs and leadership signals degrade when job pages are sparse or behind login.
- **Competitor gap risk:** proxy maturity score depends on public job-post freshness.
- **Brand tradeoff:** assertive language boosts conversion but increases overclaim risk at scale.
- **Unresolved:** full voice-channel escalation path is not yet implemented.

### Kill-Switch Metric

> If weekly overclaim rate exceeds **3 %**, pause outbound automation and re-calibrate confidence thresholds.

### Traceability Anchors

- `results/act1/trace_log.jsonl` — Act I per-task traces
- `results/act4_held_out_traces.jsonl` — Act IV held-out traces
- `results/act4_invoice_summary.json` — cost accounting
- `results/act5_evidence_graph.json` — stat test + evidence keys: ablation_confidence_aware, cost_per_task, delta_method_minus_baseline, dev_pass_at_1, heldout_pass_at_1, p_value
