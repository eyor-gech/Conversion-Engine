from __future__ import annotations

from agent.core.state import CompanyInput


def competitor_gap(company: CompanyInput, all_companies: list[CompanyInput]) -> dict[str, object]:
    peers = [c for c in all_companies if c.industry == company.industry and c.company_id != company.company_id]
    peers_sorted = sorted(peers, key=lambda c: (c.github_activity_score or 0.0), reverse=True)[:10]
    top_peers = peers_sorted[:5]

    company_caps = {role.lower() for role in company.open_roles}
    peer_caps = {role.lower() for peer in top_peers for role in peer.open_roles}
    missing = sorted(list(peer_caps - company_caps))[:8]

    ranking = [
        {
            "company": peer.name,
            "maturity_proxy": round((peer.github_activity_score or 0.0) + (len(peer.open_roles) * 0.05), 2),
        }
        for peer in top_peers
    ]

    return {
        "top_peers": [p.name for p in top_peers],
        "relative_maturity_ranking": ranking,
        "missing_capabilities": missing,
        "tone_note": "Use neutral language focused on opportunity, not deficiency.",
    }
