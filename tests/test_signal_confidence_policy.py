from __future__ import annotations

import unittest

from agent.policies.signal_confidence import apply_confidence_conditioning


class SignalConfidencePolicyTests(unittest.TestCase):
    def test_confidence_aware_prefix(self) -> None:
        txt = apply_confidence_conditioning("we found relevant demand.", confidence=0.9, mode="confidence_aware")
        self.assertTrue(txt.startswith("Based on high-confidence signals,"))

    def test_binary_threshold_prefix(self) -> None:
        txt = apply_confidence_conditioning("we found relevant demand.", confidence=0.4, mode="binary_threshold")
        self.assertTrue(txt.startswith("Based on early indicators,"))


if __name__ == "__main__":
    unittest.main()

