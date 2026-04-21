from __future__ import annotations

import json
from pathlib import Path

from agent.core.state import CompanyInput


def load_companies(path: Path) -> list[CompanyInput]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    return [CompanyInput.model_validate(item) for item in raw]
