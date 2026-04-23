from __future__ import annotations

from typing import Any


class CalComClient:
    def __init__(self, sandbox: bool = True, mock_mode: bool = True) -> None:
        self.sandbox = sandbox
        self.mock_mode = mock_mode
        self.bookings: list[dict[str, Any]] = []

    async def create_booking(self, attendee_email: str, slot_iso: str) -> dict[str, Any]:
        booking = {"attendee_email": attendee_email, "slot": slot_iso, "sandbox": self.sandbox, "mock_mode": self.mock_mode}
        self.bookings.append(booking)
        return {"status": "simulated_confirmed" if self.mock_mode else "confirmed", **booking}
