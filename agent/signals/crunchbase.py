from __future__ import annotations

from datetime import datetime, timezone

from agent.core.state import CompanyInput, SignalRecord


def funding_recency_signal(company: CompanyInput) -> SignalRecord:
    if not company.latest_funding_date:
        return SignalRecord(value=False, confidence=0.9, source="sample_companies.json", timestamp=datetime.now(timezone.utc))

    funding_dt = datetime.fromisoformat(company.latest_funding_date)
    delta_days = (datetime.now(timezone.utc) - funding_dt.replace(tzinfo=timezone.utc)).days
    recent = delta_days <= 180
    confidence = 0.92 if recent else 0.85
    return SignalRecord(value=recent, confidence=confidence, source="sample_companies.json", timestamp=datetime.now(timezone.utc))
