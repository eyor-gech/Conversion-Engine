from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from agent.core.state import CompanyInput

_AI_LEADERSHIP_TERMS = {
    "chief ai officer", "chief artificial intelligence", "vp ai", "vp of ai",
    "head of ai", "director of ai", "ai lead", "cto", "chief data officer",
}

_ROLE_MAP = {
    "cto": "cto",
    "chief technology": "cto",
    "vp engineering": "vp_engineering",
    "vp of engineering": "vp_engineering",
    "cio": "cio",
    "chief information": "cio",
    "chief data": "chief_data_officer",
    "head of ai": "head_of_ai",
    "ai officer": "head_of_ai",
    "ai lead": "head_of_ai",
}


def _infer_role(change: str) -> str:
    lower = change.lower()
    for pattern, role in _ROLE_MAP.items():
        if pattern in lower:
            return role
    return "other"


def load_leadership_signal(company: CompanyInput) -> dict[str, Any]:
    """
    Fourth enrichment source: extract and classify leadership signals from
    news/LinkedIn data stored in the company profile.

    Source: company.leadership_changes (news/LinkedIn ingestion) and
            company.exec_public_mentions (exec commentary scrape).
    Returns a typed signal dict suitable for direct inclusion in the hiring_signal_brief.
    """
    changes: list[str] = company.leadership_changes or []
    exec_mentions: list[str] = company.exec_public_mentions or []

    ai_leadership_flag = any(
        any(term in change.lower() for term in _AI_LEADERSHIP_TERMS)
        for change in changes
    )

    inferred_role = _infer_role(changes[0]) if changes else "none"

    # Confidence: high when an AI-profile title is explicitly named
    if ai_leadership_flag:
        confidence = 0.85
    elif changes:
        confidence = 0.65
    else:
        confidence = 0.40

    return {
        "detected": len(changes) > 0,
        "changes_count": len(changes),
        "changes_raw": changes,
        "ai_leadership_flag": ai_leadership_flag,
        "inferred_role": inferred_role,
        "exec_mentions_count": len(exec_mentions),
        "confidence": confidence,
        "source": "news/linkedin",
        "collected_at": datetime.now(timezone.utc).isoformat(),
    }
