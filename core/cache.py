from __future__ import annotations

import hashlib
import json
from pathlib import Path
from threading import Lock
from typing import Any


class CacheStore:
    def __init__(self, disk_path: Path | None = None) -> None:
        self._mem: dict[str, Any] = {}
        self._lock = Lock()
        self._disk_path = disk_path
        if self._disk_path is not None:
            self._disk_path.parent.mkdir(parents=True, exist_ok=True)
            if self._disk_path.exists():
                try:
                    self._mem = json.loads(self._disk_path.read_text(encoding="utf-8"))
                except Exception:
                    self._mem = {}

    def make_key(self, function_name: str, model: str, payload: Any) -> str:
        material = json.dumps(
            {"function_name": function_name, "model": model, "payload": payload},
            sort_keys=True,
            default=str,
        )
        return hashlib.sha256(material.encode("utf-8")).hexdigest()

    def get(self, key: str) -> Any | None:
        with self._lock:
            return self._mem.get(key)

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            self._mem[key] = value
            if self._disk_path is not None:
                self._disk_path.write_text(json.dumps(self._mem, indent=2, default=str), encoding="utf-8")


_GLOBAL_CACHE: CacheStore | None = None


def get_cache() -> CacheStore:
    global _GLOBAL_CACHE
    if _GLOBAL_CACHE is None:
        _GLOBAL_CACHE = CacheStore(disk_path=Path(__file__).resolve().parents[1] / "data" / "cache_store.json")
    return _GLOBAL_CACHE

