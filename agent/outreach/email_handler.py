from __future__ import annotations

from typing import Any, Awaitable, Callable

from core.event_bus import get_email_event_bus
from core.event_schema import ErrorCode
from llm.reasoning_layer import get_reasoning_layer

ReplyHandler = Callable[[dict[str, Any]], Awaitable[None] | None]


class EmailHandler:
    def __init__(self, resend_client: Any) -> None:
        self.resend_client = resend_client
        self.event_bus = get_email_event_bus()

    def onEmailReply(self, handler: ReplyHandler) -> None:
        self.event_bus.on("reply", handler)

    async def send_outbound(self, to_email: str, subject: str, body: str, metadata: dict[str, Any] | None = None) -> dict[str, Any]:
        try:
            result = await self.resend_client.send_email(to_email=to_email, subject=subject, body=body)
            await self.event_bus.emit(
                "sent",
                {"to_email": to_email, "subject": subject, "metadata": metadata or {}, "provider_response": result},
            )
            return result
        except Exception as exc:
            error_payload = {"error_type": ErrorCode.send_failure.value, "provider": "resend", "to_email": to_email, "detail": str(exc)}
            await self.event_bus.emit("error", error_payload)
            raise

    async def handle_webhook(self, payload: dict[str, Any]) -> dict[str, Any]:
        event = str(payload.get("event", "")).strip().lower()
        if not event:
            error_payload = {"error_type": ErrorCode.malformed_webhook.value, "provider": "resend", "payload": payload}
            await self.event_bus.emit("error", error_payload)
            return {"accepted": False, "error": "missing_event"}

        if event in {"bounce", "bounced"}:
            bounce_payload = {"event": "bounce", "payload": payload}
            await self.event_bus.emit("bounce", bounce_payload)
            await self.event_bus.emit("error", {"error_type": ErrorCode.bounce_event.value, "provider": "resend", "payload": payload})
            return {"accepted": True, "event": "bounce"}

        if event in {"reply", "inbound"}:
            message = str(payload.get("text") or payload.get("body") or "")
            llm_structured = await get_reasoning_layer().classify_email_reply(message=message)
            reply_payload = {"event": "reply", "raw": payload, "llm": llm_structured}
            await self.event_bus.emit("reply", reply_payload)
            return {"accepted": True, "event": "reply", "intent": llm_structured.get("intent")}

        unknown_payload = {"error_type": ErrorCode.unsupported_event.value, "provider": "resend", "payload": payload}
        await self.event_bus.emit("error", unknown_payload)
        return {"accepted": False, "error": "unsupported_event"}
