from __future__ import annotations

from agent.core.state import CompanyInput, ScoredCompany
from agent.intelligence.icp_classifier import classify_icp
from agent.signals.scoring import compute_signals


def run_signal_pipeline(company: CompanyInput, baseline_open_roles: int, icp_threshold: float) -> ScoredCompany:
    signals, ai_score, ai_expl = compute_signals(company, baseline_open_roles)
    segment, confidence, rationale = classify_icp(company, signals, icp_threshold)
    return ScoredCompany(
        company=company,
        signals=signals,
        ai_maturity_score=ai_score,
        ai_maturity_explanation=ai_expl,
        icp_segment=segment,
        icp_confidence=confidence,
        icp_rationale=rationale,
    )
