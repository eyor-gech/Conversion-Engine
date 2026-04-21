from __future__ import annotations

from agent.core.state import OutreachDraft, ScoredCompany


def generate_sms(scored: ScoredCompany) -> OutreachDraft:
    body = (
        f"Tenacious: we built a brief for {scored.company.name} based on hiring + AI signals. "
        "Open to a 15-minute walkthrough this week?"
    )
    return OutreachDraft(channel="sms", body=body, personalized_signals=["hiring_momentum", "ai_maturity"])
