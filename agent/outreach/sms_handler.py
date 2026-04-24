from __future__ import annotations

from typing import Any, Awaitable, Callable

from core.event_bus import get_sms_event_bus
from core.event_schema import ErrorCode, LeadContext
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
        lead = LeadContext.model_validate(
            {
                "prospect_id": str(lead_context.get("prospect_id", "unknown")),
                "email": lead_context.get("email"),
                "prior_email_engagement": bool(lead_context.get("prior_email_engagement")),
                "enrichment_fields": lead_context.get("enrichment_fields", {}),
            }
        )
        prior_email_engagement = lead.prior_email_engagement
        llm_eval = await get_reasoning_layer().evaluate_warm_lead(lead_context=lead.model_dump(mode="json"))
        llm_allow = bool(llm_eval.get("allow_sms"))
        llm_conf = float(llm_eval.get("confidence", 0.0))
        # Hard rule + soft reasoning.
        allow = prior_email_engagement or (llm_allow and llm_conf >= self.warm_confidence_threshold)
        return allow, llm_eval

    async def send_outbound_sms(self, to_number: str, message: str, lead_context: dict[str, Any]) -> dict[str, Any]:
        allow, llm_eval = await self._eligible_for_sms(lead_context=lead_context)
        if not allow:
            payload = {"error_type": ErrorCode.warm_lead_guard_block.value, "to_number": to_number, "llm_eval": llm_eval}
            await self.smsEventBus.emit("error", payload)
            return {"accepted": False, "reason": ErrorCode.warm_lead_guard_block.value, "llm_eval": llm_eval}

        response = await self.africastalking_client.send_sms(to_number=to_number, message=message)
        await self.smsEventBus.emit("sent", {"to_number": to_number, "message": message, "provider_response": response})
        return {"accepted": True, "provider_response": response, "llm_eval": llm_eval}

    async def handleInboundSms(self, payload: dict[str, Any]) -> dict[str, Any]:
        text = str(payload.get("text") or payload.get("message") or "").strip()
        if not text:
            error_payload = {"error_type": ErrorCode.malformed_webhook.value, "provider": "africastalking", "payload": payload}
            await self.smsEventBus.emit("error", error_payload)
            return {"accepted": False, "error": ErrorCode.missing_message.value}

        llm = await get_reasoning_layer().classify_sms_inbound(message=text)
        enriched = {"raw": payload, "llm": llm}
        await self.smsEventBus.emit("inbound", enriched)
        return {"accepted": True, "intent": llm.get("intent"), "route_hint": llm.get("route_hint")}
