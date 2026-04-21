from __future__ import annotations

from datetime import datetime, timezone

from agent.core.state import CompanyInput, SignalRecord


def layoffs_signal(company: CompanyInput) -> SignalRecord:
    return SignalRecord(
        value=company.layoffs_reported,
        confidence=0.88 if company.layoffs_reported else 0.82,
        source="layoffs.csv",
        timestamp=datetime.now(timezone.utc),
    )
