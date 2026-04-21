from __future__ import annotations

import json
from pathlib import Path


def generate(path: Path) -> None:
    rows = [
        {
            "company_id": f"mock_{i:03d}",
            "name": f"MockCompany{i}",
            "domain": f"mock{i}.example.com",
            "industry": "fintech" if i % 2 == 0 else "healthtech",
            "employee_count": 100 + i,
            "founded_year": 2010 + (i % 10),
            "latest_funding_date": "2025-10-01T00:00:00" if i % 3 == 0 else None,
            "latest_funding_round": "Series A" if i % 3 == 0 else None,
            "leadership_changes": ["New COO"] if i % 4 == 0 else [],
            "open_roles": ["AI Engineer"] if i % 5 == 0 else ["Data Analyst"],
            "layoffs_reported": i % 7 == 0,
            "tech_stack": ["AWS", "OpenAI"] if i % 5 == 0 else ["Azure"],
            "exec_public_mentions": ["AI roadmap update"] if i % 5 == 0 else ["Ops optimization"],
            "github_activity_score": round((i % 10) / 10, 2),
        }
        for i in range(1, 21)
    ]
    path.write_text(json.dumps(rows, indent=2), encoding="utf-8")


if __name__ == "__main__":
    out = Path(__file__).resolve().parents[1] / "data" / "sample_companies.generated.json"
    generate(out)
    print(f"Wrote {out}")
