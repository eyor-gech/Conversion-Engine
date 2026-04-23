from __future__ import annotations

import json
from pathlib import Path

from core.cache import get_cache


def load_job_snapshot(path: Path) -> dict[str, int]:
    cache = get_cache()
    key = cache.make_key("load_job_snapshot", "structured", {"path": str(path)})
    cached = cache.get(key)
    if cached is not None:
        return {str(k): int(v) for k, v in cached.items()}

    data = json.loads(path.read_text(encoding="utf-8"))
    cache.set(key, data)
    return {str(k): int(v) for k, v in data.items()}
