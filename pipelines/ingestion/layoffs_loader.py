from __future__ import annotations

import csv
from pathlib import Path


def load_layoff_flags(path: Path) -> dict[str, bool]:
    flags: dict[str, bool] = {}
    with path.open("r", encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            flags[row["company_id"]] = row["layoffs_reported"].strip().lower() == "true"
    return flags
