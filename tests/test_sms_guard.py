from __future__ import annotations

import asyncio
import unittest

from agent.outreach.sms_handler import SmsHandlerService
from integrations.africastalking_client import AfricasTalkingClient


class SmsGuardTests(unittest.TestCase):
    def test_blocks_cold_lead(self) -> None:
        service = SmsHandlerService(AfricasTalkingClient(mock_mode=True), warm_confidence_threshold=0.95)
        result = asyncio.run(
            service.send_outbound_sms(
                to_number="+254700000000",
                message="hello",
                lead_context={"prior_email_engagement": False},
            )
        )
        self.assertFalse(result["accepted"])
        self.assertEqual(result["reason"], "warm_lead_guard_block")


if __name__ == "__main__":
    unittest.main()

