from __future__ import annotations

from agent.core.state import ScoredCompany


def icp_score(scored: ScoredCompany) -> float:
    return scored.icp_confidence
