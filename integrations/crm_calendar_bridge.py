from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from llm.reasoning_layer import get_reasoning_layer


class CRMCalendarBridge:
    def __init__(self, hubspot_client: Any, calcom_client: Any) -> None:
        self.hubspot = hubspot_client
        self.calcom = calcom_client

    async def createBooking(self, prospect: dict[str, Any]) -> dict[str, Any]:
        booking = await self.calcom.createBooking(prospect)
        booking_summary = await get_reasoning_layer().booking_summary(
            {
                "prospect": prospect,
                "booking": booking,
            }
        )
        prospect_id = str(prospect.get("prospect_id") or prospect.get("email") or "")
        hubspot_update = await self.hubspot.update_booking_summary(
            prospect_id=prospect_id,
            booking_summary=booking_summary,
            booking_payload=booking,
        )
        return {
            "booking": booking,
            "hubspot_update": hubspot_update,
            "prospect_id": prospect_id,
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }

