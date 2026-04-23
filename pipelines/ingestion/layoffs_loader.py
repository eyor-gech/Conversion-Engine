from __future__ import annotations

import csv
from pathlib import Path


def load_layoff_flags(path: Path) -> dict[str, bool]:
    flags: dict[str, bool] = {}
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            if "company_id" in row and "layoffs_reported" in row:
                company_id = (row.get("company_id") or "").strip()
                if company_id:
                    flags[company_id] = (row.get("layoffs_reported") or "").strip().lower() == "true"
                continue
            # Backward-compatible support for public layoffs datasets with different schemas.
            company_name = (row.get("Company") or "").strip()
            if not company_name:
                continue
            laid_off = (row.get("Laid_Off_Count") or "").strip()
            percentage = (row.get("Percentage") or "").strip()
            has_layoff = bool(laid_off) or (percentage not in {"", "0", "0.0"})
            flags[company_name.lower()] = has_layoff
    return flags
