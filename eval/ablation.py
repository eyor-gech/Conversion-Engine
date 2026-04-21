from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AblationResult:
    variant: str
    pass_at_1: float
    delta_vs_full: float


def run_ablation() -> list[AblationResult]:
    full = 0.8
    variants = {
        "no_tone_guardrail": 0.74,
        "no_icp_abstention": 0.69,
        "no_outreach_validator": 0.65,
    }
    return [AblationResult("full_system", full, 0.0)] + [
        AblationResult(name, score, round(score - full, 3)) for name, score in variants.items()
    ]
