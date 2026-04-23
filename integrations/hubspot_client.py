from __future__ import annotations

from typing import Any


class HubSpotClient:
    def __init__(self, sandbox: bool = True, mock_mode: bool = True) -> None:
        self.sandbox = sandbox
        self.mock_mode = mock_mode
        self.contacts: list[dict[str, Any]] = []
        self.deals: list[dict[str, Any]] = []

    async def upsert_contact(self, email: str, name: str, company: str) -> dict[str, Any]:
        record = {"email": email, "name": name, "company": company, "sandbox": self.sandbox, "mock_mode": self.mock_mode}
        self.contacts.append(record)
        return record

    async def create_deal(self, company: str, stage: str, amount: float) -> dict[str, Any]:
        deal = {"company": company, "stage": stage, "amount": amount, "sandbox": self.sandbox, "mock_mode": self.mock_mode}
        self.deals.append(deal)
        return deal

    async def upsert_enrichment(self, prospect_id: str, icp_segment: str, signal_summary: str, enrichment_timestamp: str) -> dict[str, Any]:
        record = {
            "prospect_id": prospect_id,
            "icp_segment": icp_segment,
            "signal_enrichment_summary": signal_summary,
            "enrichment_timestamp": enrichment_timestamp,
            "sandbox": self.sandbox,
            "mock_mode": self.mock_mode,
        }
        self.contacts.append(record)
        return record

    async def update_booking_summary(self, prospect_id: str, booking_summary: str, booking_payload: dict[str, Any]) -> dict[str, Any]:
        event = {
            "prospect_id": prospect_id,
            "booking_summary": booking_summary,
            "booking_payload": booking_payload,
            "sandbox": self.sandbox,
            "mock_mode": self.mock_mode,
        }
        self.deals.append(event)
        return event
