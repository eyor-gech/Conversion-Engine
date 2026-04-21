from __future__ import annotations


def must_abstain(confidence: float, threshold: float) -> bool:
    return confidence < threshold
