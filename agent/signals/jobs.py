from __future__ import annotations

from datetime import datetime, timezone

from agent.core.state import CompanyInput, SignalRecord


def job_velocity_signal(company: CompanyInput, baseline_open_roles: int) -> SignalRecord:
    delta = len(company.open_roles) - baseline_open_roles
    # Deterministic normalization in [-1, 1]
    normalized = max(-1.0, min(1.0, delta / 10.0))
    confidence = 0.8 if baseline_open_roles > 0 else 0.7
    return SignalRecord(
        value=normalized,
        confidence=confidence,
        source="jobs_snapshot.json",
        timestamp=datetime.now(timezone.utc),
    )


def leadership_change_signal(company: CompanyInput) -> SignalRecord:
    has_change = len(company.leadership_changes) > 0
    return SignalRecord(
        value=has_change,
        confidence=0.86 if has_change else 0.76,
        source="sample_companies.json",
        timestamp=datetime.now(timezone.utc),
    )


def tech_stack_match_signal(company: CompanyInput) -> SignalRecord:
    target_stack = {"aws", "azure", "gcp", "snowflake", "databricks", "openai"}
    overlap = len(target_stack.intersection({s.lower() for s in company.tech_stack}))
    ratio = overlap / max(1, len(target_stack))
    return SignalRecord(
        value=round(ratio, 3),
        confidence=0.83,
        source="sample_companies.json",
        timestamp=datetime.now(timezone.utc),
    )
