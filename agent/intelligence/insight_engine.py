from __future__ import annotations

from agent.core.state import CompanyInput, ScoredCompany
from agent.intelligence.competitor_gap import competitor_gap
from agent.intelligence.hiring_brief import generate_hiring_brief


def build_insight_packet(scored: ScoredCompany, universe: list[CompanyInput]) -> dict[str, object]:
    return {
        "hiring_brief": generate_hiring_brief(scored.company, scored.signals),
        "competitor_gap": competitor_gap(scored.company, universe),
        "icp_rationale": scored.icp_rationale,
        "ai_maturity_explanation": scored.ai_maturity_explanation,
    }
