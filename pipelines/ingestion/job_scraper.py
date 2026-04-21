from __future__ import annotations

import json
from pathlib import Path


def load_job_snapshot(path: Path) -> dict[str, int]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return {str(k): int(v) for k, v in data.items()}
