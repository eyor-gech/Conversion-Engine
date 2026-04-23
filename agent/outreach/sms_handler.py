from __future__ import annotations

from typing import Any, Awaitable, Callable

from core.event_bus import get_sms_event_bus
from llm.reasoning_layer import get_reasoning_layer

SmsHandler = Callable[[dict[str, Any]], Awaitable[None] | None]


class SmsHandlerService:
    def __init__(self, africastalking_client: Any, warm_confidence_threshold: float = 0.7) -> None:
        self.africastalking_client = africastalking_client
        self.warm_confidence_threshold = warm_confidence_threshold
        self.smsEventBus = get_sms_event_bus()

    def onInboundSms(self, handler: SmsHandler) -> None:
        self.smsEventBus.on("inbound", handler)

    async def _eligible_for_sms(self, lead_context: dict[str, Any]) -> tuple[bool, dict[str, Any]]:
        prior_email_engagement = bool(lead_context.get("prior_email_engagement"))
        llm_eval = await get_reasoning_layer().evaluate_warm_lead(lead_context=lead_context)
        llm_allow = bool(llm_eval.get("allow_sms"))
        llm_conf = float(llm_eval.get("confidence", 0.0))
        # Hard rule + soft reasoning.
        allow = prior_email_engagement or (llm_allow and llm_conf >= self.warm_confidence_threshold)
        return allow, llm_eval

    async def send_outbound_sms(self, to_number: str, message: str, lead_context: dict[str, Any]) -> dict[str, Any]:
        allow, llm_eval = await self._eligible_for_sms(lead_context=lead_context)
        if not allow:
            payload = {"error_type": "warm_lead_guard_block", "to_number": to_number, "llm_eval": llm_eval}
            await self.smsEventBus.emit("error", payload)
            return {"accepted": False, "reason": "warm_lead_guard_block", "llm_eval": llm_eval}

        response = await self.africastalking_client.send_sms(to_number=to_number, message=message)
        await self.smsEventBus.emit("sent", {"to_number": to_number, "message": message, "provider_response": response})
        return {"accepted": True, "provider_response": response, "llm_eval": llm_eval}

    async def handleInboundSms(self, payload: dict[str, Any]) -> dict[str, Any]:
        text = str(payload.get("text") or payload.get("message") or "").strip()
        if not text:
            error_payload = {"error_type": "malformed_webhook", "provider": "africastalking", "payload": payload}
            await self.smsEventBus.emit("error", error_payload)
            return {"accepted": False, "error": "missing_message"}

        llm = await get_reasoning_layer().classify_sms_inbound(message=text)
        enriched = {"raw": payload, "llm": llm}
        await self.smsEventBus.emit("inbound", enriched)
        return {"accepted": True, "intent": llm.get("intent"), "route_hint": llm.get("route_hint")}

