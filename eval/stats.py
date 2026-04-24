from __future__ import annotations

import random
from statistics import mean
from typing import Iterable


def bootstrap_ci(values: list[float], n_resamples: int = 10_000, alpha: float = 0.05, seed: int = 42) -> tuple[float, float]:
    if not values:
        return 0.0, 0.0
    rng = random.Random(seed)
    resampled_means: list[float] = []
    n = len(values)
    for _ in range(n_resamples):
        sample = [values[rng.randrange(0, n)] for _ in range(n)]
        resampled_means.append(mean(sample))
    resampled_means.sort()
    low_idx = int((alpha / 2) * n_resamples)
    high_idx = int((1 - alpha / 2) * n_resamples) - 1
    return float(resampled_means[low_idx]), float(resampled_means[high_idx])


def bootstrap_difference_p_value(
    baseline: list[float],
    method: list[float],
    n_resamples: int = 10_000,
    seed: int = 42,
) -> dict[str, float]:
    if not baseline or not method:
        return {"delta": 0.0, "p_value": 1.0, "ci_low": 0.0, "ci_high": 0.0}
    rng = random.Random(seed)
    b_n = len(baseline)
    m_n = len(method)
    deltas: list[float] = []
    for _ in range(n_resamples):
        b = [baseline[rng.randrange(0, b_n)] for _ in range(b_n)]
        m = [method[rng.randrange(0, m_n)] for _ in range(m_n)]
        deltas.append(mean(m) - mean(b))
    deltas.sort()
    observed = mean(method) - mean(baseline)
    p = sum(1 for d in deltas if d <= 0.0) / len(deltas)
    low = deltas[int(0.025 * n_resamples)]
    high = deltas[int(0.975 * n_resamples) - 1]
    return {"delta": float(observed), "p_value": float(p), "ci_low": float(low), "ci_high": float(high)}

