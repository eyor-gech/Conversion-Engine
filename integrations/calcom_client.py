from __future__ import annotations

from typing import Any


class CalComClient:
    def __init__(self, sandbox: bool = True) -> None:
        self.sandbox = sandbox
        self.bookings: list[dict[str, Any]] = []

    async def create_booking(self, attendee_email: str, slot_iso: str) -> dict[str, Any]:
        booking = {"attendee_email": attendee_email, "slot": slot_iso, "sandbox": self.sandbox}
        self.bookings.append(booking)
        return {"status": "confirmed", **booking}
