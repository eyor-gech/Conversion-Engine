"""
Regenerate act2_competitor_gap_brief.json using the updated schema-compliant
competitor_gap() function. Uses existing sample_companies.json data — no API calls needed.
"""
from __future__ import annotations

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

companies_raw = json.loads((BASE / "data" / "sample_companies.json").read_text(encoding="utf-8"))
companies = [CompanyInput(**c) for c in companies_raw]

prospect = companies[0]
universe = companies

brief = competitor_gap(prospect, universe)

out = BASE / "results" / "act2_competitor_gap_brief.json"
out.write_text(json.dumps(brief, indent=2, default=str), encoding="utf-8")
print(f"Written: {out}")
print(f"  prospect_domain: {brief['prospect_domain']}")
print(f"  prospect_sector: {brief['prospect_sector']}")
print(f"  prospect_ai_maturity_score: {brief['prospect_ai_maturity_score']}")
print(f"  sector_top_quartile_benchmark: {brief['sector_top_quartile_benchmark']}")
print(f"  competitors_analyzed: {len(brief['competitors_analyzed'])} peers")
print(f"  gap_findings: {len(brief['gap_findings'])} findings")
for gf in brief["gap_findings"]:
    print(f"    - {gf['practice'][:80]}  confidence={gf['confidence']}")
    for ev in gf["peer_evidence"]:
        print(f"      * {ev['competitor_name']}: {ev['source_url']}")
print(f"  gap_quality_self_check: {brief['gap_quality_self_check']}")
