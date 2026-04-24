from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from agent.core.orchestrator import build_orchestrator
from agent.enrichment import run_enrichment
from agent.outreach.email_handler import EmailHandler
from agent.outreach.sms_handler import SmsHandlerService
from agent.policies.signal_confidence import apply_confidence_conditioning
from llm.reasoning_layer import get_reasoning_layer
from pipelines.ingestion.crunchbase_loader import load_companies


async def run_single_synthetic_thread(output_dir: Path) -> dict[str, Any]:
    orch = build_orchestrator()
    companies = load_companies(orch.paths.data_dir / "sample_companies.json")
    target = companies[0]

    briefs = await run_enrichment(target, companies, output_dir=output_dir)
    confidence = float(
        briefs["hiring_signal_brief"]["signals"]["jobPosts"]["confidenceScore"]  # type: ignore[index]
    )

    email_handler = EmailHandler(orch.resend)
    sms_handler = SmsHandlerService(orch.sms)

    base_email = (
        f"Hi {target.name} team, we prepared an outreach brief from hiring and competitor signals "
        "and can walk through practical next steps this week."
    )
    conditioned_email = apply_confidence_conditioning(base_email, confidence=confidence, mode="confidence_aware")
    email_send = await email_handler.send_outbound(
        to_email=f"partnerships@{target.domain}",
        subject=f"{target.name} growth brief",
        body=conditioned_email,
    )

    reply_payload = {"event": "reply", "body": "Thanks, interested. Can we book Thursday 2pm?"}
    reply_result = await email_handler.handle_webhook(reply_payload)
    qualification = await get_reasoning_layer().classify_email_reply(reply_payload["body"])

    sms_result = await sms_handler.send_outbound_sms(
        to_number="+254700000000",
        message="Happy to share a booking link for Thursday options.",
        lead_context={"prior_email_engagement": True, "prospect_id": target.company_id},
    )

    booking = await orch.crm_calendar_bridge.createBooking(
        {
            "prospect_id": target.company_id,
            "email": f"partnerships@{target.domain}",
            "slot_iso": "2026-05-01T11:00:00Z",
            "timezone": "Africa/Nairobi",
        }
    )

    thread = {
        "thread_id": f"thread-{target.company_id}",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "prospect_id": target.company_id,
        "email_send": email_send,
        "email_reply": reply_result,
        "qualification": qualification,
        "sms": sms_result,
        "booking": booking,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "sample_thread.json").write_text(json.dumps(thread, indent=2, default=str), encoding="utf-8")
    return thread

