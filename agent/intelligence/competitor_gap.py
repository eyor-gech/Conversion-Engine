from __future__ import annotations

from agent.core.state import CompanyInput
from core.cache import get_cache

_SPARSE_PEER_THRESHOLD = 3


def _maturity_proxy(c: CompanyInput) -> float:
    return round((c.github_activity_score or 0.0) + (len(c.open_roles) * 0.05), 2)


def competitor_gap(company: CompanyInput, all_companies: list[CompanyInput]) -> dict[str, object]:
    cache = get_cache()
    key = cache.make_key(
        "competitor_gap",
        "v2",
        {
            "company": company.model_dump(mode="json"),
            "universe": [c.model_dump(mode="json") for c in all_companies],
        },
    )
    cached = cache.get(key)
    if cached is not None:
        return dict(cached)

    same_industry_peers = [
        c for c in all_companies if c.industry == company.industry and c.company_id != company.company_id
    ]
    universe = [c for c in all_companies if c.company_id != company.company_id]

    # Sparse sector: fall back to cross-industry peers when fewer than 3 same-sector peers
    if len(same_industry_peers) < _SPARSE_PEER_THRESHOLD:
        peer_pool = universe
        sparse_note = (
            f"Sparse sector ({company.industry!r}): only {len(same_industry_peers)} same-industry peer(s) found; "
            "cross-sector peers used for ranking. Interpret capability gaps with caution."
        )
    else:
        peer_pool = same_industry_peers
        sparse_note = None

    peers_sorted = sorted(peer_pool, key=_maturity_proxy, reverse=True)[:10]
    top_peers = peers_sorted[:5]

    # Capability gap: derived from public job post titles (jobs_snapshot.json)
    company_caps = {role.lower() for role in company.open_roles}
    peer_caps = {role.lower() for peer in top_peers for role in peer.open_roles}
    missing = sorted(list(peer_caps - company_caps))[:8]

    ranking = [
        {"company": peer.name, "maturity_proxy": _maturity_proxy(peer)}
        for peer in top_peers
    ]

    # Distribution position: percentile of this company among entire universe
    company_proxy = _maturity_proxy(company)
    all_proxies = [_maturity_proxy(c) for c in universe]
    below = sum(1 for p in all_proxies if p < company_proxy)
    percentile = round((below / len(all_proxies)) * 100, 1) if all_proxies else 50.0

    result: dict[str, object] = {
        "top_peers": [p.name for p in top_peers],
        "relative_maturity_ranking": ranking,
        "missing_capabilities": missing,
        "distribution_position": {
            "percentile": percentile,
            "maturity_proxy_score": company_proxy,
            "universe_size": len(universe),
            "note": (
                f"{company.name} ranks at the {percentile}th percentile across "
                f"{len(universe)} companies by maturity proxy score."
            ),
        },
        "evidence_note": (
            "Capability gaps derived from public job post titles via structured data snapshot "
            "(data/jobs_snapshot.json). Same scoring function (github_activity_score + role count) "
            "as AI maturity pipeline."
        ),
        "tone_note": "Use neutral language focused on opportunity, not deficiency.",
    }
    if sparse_note:
        result["sparse_sector_note"] = sparse_note

    cache.set(key, result)
    return result
