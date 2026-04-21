from __future__ import annotations

from typing import Any


class HubSpotClient:
    def __init__(self, sandbox: bool = True) -> None:
        self.sandbox = sandbox
        self.contacts: list[dict[str, Any]] = []
        self.deals: list[dict[str, Any]] = []

    async def upsert_contact(self, email: str, name: str, company: str) -> dict[str, Any]:
        record = {"email": email, "name": name, "company": company, "sandbox": self.sandbox}
        self.contacts.append(record)
        return record

    async def create_deal(self, company: str, stage: str, amount: float) -> dict[str, Any]:
        deal = {"company": company, "stage": stage, "amount": amount, "sandbox": self.sandbox}
        self.deals.append(deal)
        return deal
