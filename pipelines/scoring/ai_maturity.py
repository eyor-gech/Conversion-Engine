from __future__ import annotations

from agent.core.state import ScoredCompany


def ai_maturity_score(scored: ScoredCompany) -> int:
    return scored.ai_maturity_score
