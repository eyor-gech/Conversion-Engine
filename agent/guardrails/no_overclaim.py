from __future__ import annotations


def detect_overclaim(text: str) -> bool:
    risky = ["guarantee", "certain", "always", "no risk", "100%"]
    lowered = text.lower()
    return any(token in lowered for token in risky)
