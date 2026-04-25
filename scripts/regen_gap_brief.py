"""
Regenerate act2_competitor_gap_brief.json and act2_hiring_signal_brief.json
using the updated schema-compliant functions. Uses existing sample_companies.json
data — no external API calls needed.
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE))

import os
os.environ.setdefault("MOCK_MODE", "false")

try:
    from dotenv import load_dotenv
    load_dotenv(BASE / ".env", override=True)
except Exception:
    pass

from agent.core.state import CompanyInput
from agent.intelligence.competitor_gap import competitor_gap
from agent.enrichment import run_enrichment


companies_raw = json.loads((BASE / "data" / "sample_companies.json").read_text(encoding="utf-8"))
companies = [CompanyInput(**c) for c in companies_raw]

prospect = companies[0]
universe = companies

# Competitor gap brief
brief = competitor_gap(prospect, universe)
out = BASE / "results" / "act2_competitor_gap_brief.json"
out.write_text(json.dumps(brief, indent=2, default=str), encoding="utf-8")
print(f"Written: {out}")
print(f"  prospect_domain: {brief['prospect_domain']}")
print(f"  sector_top_quartile_benchmark: {brief['sector_top_quartile_benchmark']}")
print(f"  competitors_analyzed: {len(brief['competitors_analyzed'])} peers")
print(f"  gap_findings: {len(brief['gap_findings'])} findings")


# Hiring signal brief (async)
async def regen_hiring():
    output_dir = BASE / "results" / "act2_regen"
    briefs = await run_enrichment(prospect, universe, output_dir=output_dir)
    hsb = briefs["hiring_signal_brief"]

    # Save to results/
    out_hsb = BASE / "results" / "act2_hiring_signal_brief.json"
    out_hsb.write_text(json.dumps(hsb, indent=2, default=str), encoding="utf-8")
    print(f"\nWritten: {out_hsb}")
    print(f"  prospect_domain: {hsb['prospect_domain']}")
    print(f"  primary_segment_match: {hsb['primary_segment_match']}  confidence={hsb['segment_confidence']}")
    print(f"  ai_maturity.score: {hsb['ai_maturity']['score']}")
    hv = hsb["hiring_velocity"]
    print(f"  hiring_velocity: today={hv['open_roles_today']} 60d_ago={hv['open_roles_60_days_ago']} label={hv['velocity_label']}")
    print(f"  data_sources_checked: {len(hsb['data_sources_checked'])} sources")
    for ds in hsb["data_sources_checked"]:
        print(f"    {ds['source']}: {ds['status']}  fetched_at={ds['fetched_at']}")

asyncio.run(regen_hiring())
