from __future__ import annotations

from agent.core.state import OutreachDraft, ScoredCompany


def generate_email(scored: ScoredCompany, insight_packet: dict[str, object]) -> OutreachDraft:
    company = scored.company
    subject = f"{company.name} hiring momentum + AI enablement"
    body = (
        f"Hi {company.name} team,\n\n"
        f"We noticed structured signals showing hiring movement and a growing AI footprint at {company.name}. "
        "Tenacious helps teams convert those signals into repeatable revenue workflows without adding process drag.\n\n"
        f"From current evidence: ICP segment={scored.icp_segment}, AI maturity={scored.ai_maturity_score}/3.\n"
        "If useful, we can share a short benchmark-backed plan tailored to your current stage.\n\n"
        "Best,\nTenacious Consulting"
    )
    return OutreachDraft(
        channel="email",
        subject=subject,
        body=body,
        personalized_signals=["hiring_momentum", "ai_maturity", "icp_segment"],
    )
