from __future__ import annotations

import json
import unittest
from pathlib import Path


class ProbeRegressionTests(unittest.TestCase):
    def test_probe_library_size(self) -> None:
        path = Path(__file__).resolve().parents[1] / "probes" / "probe_cases.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        self.assertGreaterEqual(len(data), 30)


if __name__ == "__main__":
    unittest.main()

