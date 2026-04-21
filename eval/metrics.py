from __future__ import annotations

from math import sqrt


def wilson_ci(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    p = successes / total
    denom = 1 + (z**2 / total)
    center = p + (z**2 / (2 * total))
    margin = z * sqrt((p * (1 - p) / total) + (z**2 / (4 * total**2)))
    low = (center - margin) / denom
    high = (center + margin) / denom
    return max(0.0, low), min(1.0, high)
