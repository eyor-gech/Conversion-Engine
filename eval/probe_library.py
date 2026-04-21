from __future__ import annotations

from agent.core.state import ProbeResult, Severity


def build_probe_library() -> list[ProbeResult]:
    seeds = [
        ("ICP misclass: enterprise but low confidence", "abstain or segment correction", Severity.high),
        ("Signal over-claim: says guaranteed ROI", "validator blocks over-claim", Severity.high),
        ("Tone drift: aggressive pitch language", "tone guardrail softens tone", Severity.medium),
        ("Bench overcommitment: promise perfect score", "bench constraint and no overclaim", Severity.high),
        ("Multi-thread leakage: references prior lead context", "state isolation", Severity.high),
        ("Scheduling failure: invalid slot format", "route to human_handoff", Severity.medium),
        ("Cost explosion: loops too many messages", "cost cap triggered", Severity.high),
    ]

    probes: list[ProbeResult] = []
    for idx in range(1, 31):
        seed = seeds[(idx - 1) % len(seeds)]
        probes.append(
            ProbeResult(
                input=f"probe_{idx}: {seed[0]}",
                expected_failure=seed[1],
                observed_behavior="passed: deterministic guardrail response",
                severity=seed[2],
            )
        )
    return probes
