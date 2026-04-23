from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from agent.core.state import CompanyInput
from llm.reasoning_layer import get_reasoning_layer


async def build_unified_signal_schema(company: CompanyInput) -> dict[str, dict[str, Any]]:
    llm = get_reasoning_layer()

    crunchbase_raw = company.model_dump(mode="json")
    crunchbase_normalized = await llm.normalize_crunchbase_profile(crunchbase_raw)

    jobs_payload = {"company_id": company.company_id, "open_roles": company.open_roles}
    jobs_llm = await llm.classify_jobs_and_hiring_intent(jobs_payload)

    layoffs_payload = {"company_id": company.company_id, "layoffs_reported": company.layoffs_reported, "industry": company.industry}
    layoffs_llm = await llm.classify_layoff_severity(layoffs_payload)

    leadership_payload = {
        "company_id": company.company_id,
        "leadership_changes": company.leadership_changes,
        "exec_public_mentions": company.exec_public_mentions,
    }
    leadership_llm = await llm.infer_leadership_change(leadership_payload)

    return {
        "crunchbase": {
            "payload": crunchbase_normalized,
            "confidenceScore": float(crunchbase_normalized.get("confidence", 0.7) if isinstance(crunchbase_normalized, dict) else 0.7),
            "source": "crunchbase",
        },
        "jobPosts": {
            "payload": jobs_llm,
            "confidenceScore": float(jobs_llm.get("confidence", 0.65)),
            "source": "jobs",
        },
        "layoffs": {
            "payload": layoffs_llm,
            "confidenceScore": float(layoffs_llm.get("confidence", 0.62)),
            "source": "layoffs.fyi",
        },
        "leadershipChanges": {
            "payload": {
                "detected_at": datetime.now(timezone.utc).isoformat(),
                "changes": company.leadership_changes,
                "llm_confirmation": leadership_llm,
            },
            "confidenceScore": float(leadership_llm.get("confidence", 0.6)),
            "source": "news/signal",
        },
    }

