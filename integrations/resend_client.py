from __future__ import annotations

from typing import Any


class ResendClient:
    def __init__(self, sandbox: bool = True) -> None:
        self.sandbox = sandbox
        self.sent: list[dict[str, Any]] = []

    async def send_email(self, to_email: str, subject: str, body: str) -> dict[str, Any]:
        payload = {"to": to_email, "subject": subject, "body": body, "sandbox": self.sandbox}
        self.sent.append(payload)
        return {"status": "queued", **payload}
