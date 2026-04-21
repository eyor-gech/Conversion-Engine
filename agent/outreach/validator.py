from __future__ import annotations

from agent.core.state import OutreachDraft, ScoredCompany, ValidatorResult


def validate_outreach(draft: OutreachDraft, scored: ScoredCompany) -> ValidatorResult:
    reasons: list[str] = []
    text = f"{draft.subject or ''} {draft.body}".lower()

    banned_claims = ["guarantee", "100%", "certain", "no risk"]
    for claim in banned_claims:
        if claim in text:
            reasons.append(f"over-claim detected: {claim}")

    if "hiring" in text and "job_velocity" not in scored.signals:
        reasons.append("unsupported hiring assertion")

    if scored.icp_segment == "abstain":
        reasons.append("mismatched ICP messaging due to abstention")

    return ValidatorResult(accepted=len(reasons) == 0, reasons=reasons)
