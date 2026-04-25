from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from agent.core.state import CompanyInput
from llm.reasoning_layer import get_reasoning_layer
from pipelines.ingestion.leadership_loader import load_leadership_signal


async def build_unified_signal_schema(company: CompanyInput) -> dict[str, dict[str, Any]]:
    """
    Build the four-source enriched signal schema for a prospect company.

    Sources (one module per signal):
      1. crunchbase       — company profile normalization via LLM
      2. jobs             — job-post hiring-intent classification via LLM
      3. layoffs.fyi      — layoff severity classification via LLM
      4. news/linkedin    — leadership signal extraction via leadership_loader
    """
    llm = get_reasoning_layer()
    now = datetime.now(timezone.utc).isoformat()

    # Signal 1: Crunchbase company profile
    crunchbase_raw = company.model_dump(mode="json")
    crunchbase_normalized = await llm.normalize_crunchbase_profile(crunchbase_raw)
    crunchbase_confidence = float(
        crunchbase_normalized.get("confidence", 0.7)
        if isinstance(crunchbase_normalized, dict) else 0.7
    )

    # Signal 2: Job posts (hiring intent from structured job snapshot)
    jobs_payload = {"company_id": company.company_id, "open_roles": company.open_roles}
    jobs_llm = await llm.classify_jobs_and_hiring_intent(jobs_payload)
    jobs_confidence = float(jobs_llm.get("confidence", 0.65))

    # Signal 3: Layoffs signal (severity classification)
    layoffs_payload = {
        "company_id": company.company_id,
        "layoffs_reported": company.layoffs_reported,
        "industry": company.industry,
    }
    layoffs_llm = await llm.classify_layoff_severity(layoffs_payload)
    layoffs_confidence = float(layoffs_llm.get("confidence", 0.62))

    # Signal 4: Leadership signal (dedicated leadership_loader module)
    leadership_data = load_leadership_signal(company)
    leadership_llm = await llm.infer_leadership_change({
        "company_id": company.company_id,
        "leadership_changes": company.leadership_changes,
        "exec_public_mentions": company.exec_public_mentions,
    })
    leadership_confidence = float(leadership_llm.get("confidence", leadership_data["confidence"]))

    return {
        "crunchbase": {
            "payload": crunchbase_normalized,
            "confidence": crunchbase_confidence,
            "confidenceScore": crunchbase_confidence,  # backward compat alias
            "source": "crunchbase",
            "collected_at": now,
        },
        "jobPosts": {
            "payload": jobs_llm,
            "confidence": jobs_confidence,
            "confidenceScore": jobs_confidence,  # backward compat alias
            "source": "jobs_snapshot / careers_page",
            "collected_at": now,
        },
        "layoffs": {
            "payload": layoffs_llm,
            "confidence": layoffs_confidence,
            "confidenceScore": layoffs_confidence,  # backward compat alias
            "source": "layoffs.fyi",
            "collected_at": now,
        },
        "leadershipChanges": {
            "payload": {
                "structured": leadership_data,
                "llm_confirmation": leadership_llm,
            },
            "confidence": leadership_confidence,
            "confidenceScore": leadership_confidence,  # backward compat alias
            "source": "news/linkedin",
            "collected_at": now,
        },
    }
