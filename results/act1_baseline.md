# Act I Baseline

Reproduced retail-domain dev-slice evaluation from local τ² task data (30 tasks, 1 trial/task) using the repository harness and OpenRouter-backed LLM routing.

- Model: openai/gpt-4o-mini
- pass@1 mean: 0.5333
- 95% CI (bootstrap, 10,000 resamples): [0.3667, 0.7]
- Cost per run (USD): 0.005076
- Latency p50/p95 (ms): 6249.629 / 8705.07
- Logged every trajectory to eval/trace_log.jsonl with trace IDs.
- Logs are also emitted through Langfuse-compatible trace events in-process.

Anomalies: no hard tool-execution verifier is currently integrated into this harness; success is measured from structured response availability and non-fallback output status.
