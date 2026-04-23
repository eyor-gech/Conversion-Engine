from __future__ import annotations

from typing import Any


class ResendClient:
    def __init__(self, sandbox: bool = True, mock_mode: bool = True) -> None:
        self.sandbox = sandbox
        self.mock_mode = mock_mode
        self.sent: list[dict[str, Any]] = []

    async def send_email(self, to_email: str, subject: str, body: str) -> dict[str, Any]:
        payload = {"to": to_email, "subject": subject, "body": body, "sandbox": self.sandbox, "mock_mode": self.mock_mode}
        self.sent.append(payload)
        return {"status": "simulated_queued" if self.mock_mode else "queued", **payload}
