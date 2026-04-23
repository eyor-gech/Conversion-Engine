from __future__ import annotations

import json
from pathlib import Path

from agent.core.state import CompanyInput
from core.cache import get_cache


def load_companies(path: Path) -> list[CompanyInput]:
    cache = get_cache()
    key = cache.make_key("load_companies", "structured", {"path": str(path)})
    cached = cache.get(key)
    if cached is not None:
        return [CompanyInput.model_validate(item) for item in cached]

    raw = json.loads(path.read_text(encoding="utf-8"))
    cache.set(key, raw)
    return [CompanyInput.model_validate(item) for item in raw]
