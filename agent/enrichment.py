from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent.core.state import CompanyInput
from agent.intelligence.competitor_gap import competitor_gap
from pipelines.enrichment.unified_signal_enrichment import build_unified_signal_schema


async def run_enrichment(company: CompanyInput, universe: list[CompanyInput], output_dir: Path) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)
    unified = await build_unified_signal_schema(company)
    gap = competitor_gap(company, universe)

    hiring_signal_brief = {
        "company": {"name": company.name, "domain": company.domain},
        "signals": unified,
        "justification": "Signals merged from structured ingestion and LLM reasoning layer.",
    }
    # gap is already schema-compliant (prospect_domain, prospect_sector, competitors_analyzed, etc.)
    competitor_gap_brief = gap

    (output_dir / "hiring_signal_brief.json").write_text(
        json.dumps(hiring_signal_brief, indent=2, default=str),
        encoding="utf-8",
    )
    (output_dir / "competitor_gap_brief.json").write_text(
        json.dumps(competitor_gap_brief, indent=2, default=str),
        encoding="utf-8",
    )
    return {
        "hiring_signal_brief": hiring_signal_brief,
        "competitor_gap_brief": competitor_gap_brief,
    }

