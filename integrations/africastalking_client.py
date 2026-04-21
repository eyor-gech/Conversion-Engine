from __future__ import annotations

from typing import Any


class AfricasTalkingClient:
    def __init__(self, sandbox: bool = True) -> None:
        self.sandbox = sandbox
        self.sent: list[dict[str, Any]] = []

    async def send_sms(self, to_number: str, message: str) -> dict[str, Any]:
        payload = {"to": to_number, "message": message, "sandbox": self.sandbox}
        self.sent.append(payload)
        return {"status": "queued", **payload}
