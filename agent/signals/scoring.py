from __future__ import annotations

from agent.core.state import CompanyInput, SignalRecord
from agent.signals.ai_maturity import score_ai_maturity
from agent.signals.crunchbase import funding_recency_signal
from agent.signals.jobs import job_velocity_signal, leadership_change_signal, tech_stack_match_signal
from agent.signals.layoffs import layoffs_signal


def compute_signals(company: CompanyInput, baseline_open_roles: int) -> tuple[dict[str, SignalRecord], int, str]:
    signals = {
        "funding_recency": funding_recency_signal(company),
        "job_velocity": job_velocity_signal(company, baseline_open_roles),
        "layoffs": layoffs_signal(company),
        "leadership_change": leadership_change_signal(company),
        "tech_stack_match": tech_stack_match_signal(company),
    }
    ai_score, explanation = score_ai_maturity(company)
    signals["ai_maturity"] = SignalRecord(
        value=ai_score,
        confidence=0.84,
        source="derived:ai_maturity",
        timestamp=signals["funding_recency"].timestamp,
    )
    return signals, ai_score, explanation
