from __future__ import annotations

import json
from typing import Any

from llm.openrouter_client import get_openrouter_client


def _extract_json(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    if stripped.startswith("{") and stripped.endswith("}"):
        try:
            return json.loads(stripped)
        except json.JSONDecodeError:
            return None
    return None


class LLMReasoningLayer:
    async def classify_icp_segment(self, company_payload: dict[str, Any]) -> dict[str, Any]:
        prompt = (
            "Classify ICP segment from company payload. Return JSON only with keys: segment, confidence, rationale.\n"
            f"{json.dumps(company_payload, default=str)}"
        )
        result = await get_openrouter_client().complete(
            task_type="classification",
            prompt=prompt,
            function_name="classify_icp_segment",
        )
        parsed = _extract_json(str(result.get("text", "")))
        if parsed:
            return parsed
        industry = str(company_payload.get("industry", "")).lower()
        segment = "segment_1" if industry in {"fintech", "healthtech"} else "segment_4"
        return {"segment": segment, "confidence": 0.6, "rationale": "fallback industry heuristic"}

    async def classify_email_reply(self, message: str) -> dict[str, Any]:
        prompt = (
            "Classify email reply intent and sentiment. Return JSON only with keys: "
            "intent, sentiment, confidence, structured_response.\n"
            f"Message: {message}"
        )
        result = await get_openrouter_client().complete(
            task_type="classification",
            prompt=prompt,
            function_name="classify_email_reply",
        )
        parsed = _extract_json(str(result.get("text", "")))
        if parsed:
            return parsed
        text = message.lower()
        intent = "book_meeting" if "meeting" in text else "unknown"
        sentiment = "positive" if any(k in text for k in ["yes", "great", "interested"]) else "neutral"
        return {
            "intent": intent,
            "sentiment": sentiment,
            "confidence": 0.6,
            "structured_response": {"raw": message},
        }

    async def classify_sms_inbound(self, message: str) -> dict[str, Any]:
        prompt = (
            "Classify inbound sms intent. Return JSON only with keys: intent, confidence, route_hint.\n"
            f"SMS: {message}"
        )
        result = await get_openrouter_client().complete(
            task_type="classification",
            prompt=prompt,
            function_name="classify_sms_inbound",
        )
        parsed = _extract_json(str(result.get("text", "")))
        if parsed:
            return parsed
        text = message.lower()
        intent = "unsubscribe" if "stop" in text else ("book_meeting" if "book" in text else "unknown")
        return {"intent": intent, "confidence": 0.58, "route_hint": "conversation_engine"}

    async def evaluate_warm_lead(self, lead_context: dict[str, Any]) -> dict[str, Any]:
        prompt = (
            "Given the lead context, decide if sms warm outreach is appropriate. "
            "Return JSON only with: allow_sms, confidence, reason.\n"
            f"Lead context: {json.dumps(lead_context, default=str)}"
        )
        result = await get_openrouter_client().complete(
            task_type="reasoning",
            prompt=prompt,
            function_name="evaluate_warm_lead",
        )
        parsed = _extract_json(str(result.get("text", "")))
        if parsed:
            return parsed
        prior = bool(lead_context.get("prior_email_engagement"))
        return {"allow_sms": prior, "confidence": 0.55 if prior else 0.45, "reason": "fallback heuristic"}

    async def normalize_crunchbase_profile(self, raw_profile: dict[str, Any]) -> dict[str, Any]:
        prompt = (
            "Normalize this company profile into concise canonical fields. Return JSON only.\n"
            f"{json.dumps(raw_profile, default=str)}"
        )
        result = await get_openrouter_client().complete(
            task_type="summarization",
            prompt=prompt,
            function_name="normalize_crunchbase_profile",
        )
        parsed = _extract_json(str(result.get("text", "")))
        if parsed:
            return parsed
        return {
            "name": raw_profile.get("name"),
            "industry": raw_profile.get("industry"),
            "employee_count": raw_profile.get("employee_count"),
            "summary": "normalized_fallback",
        }

    async def classify_jobs_and_hiring_intent(self, jobs_payload: dict[str, Any]) -> dict[str, Any]:
        prompt = (
            "Infer job-role categories and hiring intent from payload. Return JSON with keys: "
            "role_categories, hiring_intent, confidence.\n"
            f"{json.dumps(jobs_payload, default=str)}"
        )
        result = await get_openrouter_client().complete(
            task_type="reasoning",
            prompt=prompt,
            function_name="classify_jobs_and_hiring_intent",
        )
        parsed = _extract_json(str(result.get("text", "")))
        if parsed:
            return parsed
        open_roles = jobs_payload.get("open_roles", [])
        ai_roles = [role for role in open_roles if "ai" in str(role).lower() or "ml" in str(role).lower()]
        return {
            "role_categories": {"ai_ml": len(ai_roles), "other": max(0, len(open_roles) - len(ai_roles))},
            "hiring_intent": "expansion" if len(open_roles) >= 2 else "steady",
            "confidence": 0.62,
        }

    async def classify_layoff_severity(self, layoffs_payload: dict[str, Any]) -> dict[str, Any]:
        prompt = (
            "Classify layoff severity and industry impact. Return JSON with keys: severity, impact_reasoning, confidence.\n"
            f"{json.dumps(layoffs_payload, default=str)}"
        )
        result = await get_openrouter_client().complete(
            task_type="reasoning",
            prompt=prompt,
            function_name="classify_layoff_severity",
        )
        parsed = _extract_json(str(result.get("text", "")))
        if parsed:
            return parsed
        reported = bool(layoffs_payload.get("layoffs_reported"))
        return {
            "severity": "high" if reported else "low",
            "impact_reasoning": "fallback classification from structured layoffs flag",
            "confidence": 0.61,
        }

    async def infer_leadership_change(self, leadership_payload: dict[str, Any]) -> dict[str, Any]:
        prompt = (
            "Infer if leadership change is meaningful for outbound timing. Return JSON with keys: "
            "confirmed, rationale, confidence.\n"
            f"{json.dumps(leadership_payload, default=str)}"
        )
        result = await get_openrouter_client().complete(
            task_type="reasoning",
            prompt=prompt,
            function_name="infer_leadership_change",
        )
        parsed = _extract_json(str(result.get("text", "")))
        if parsed:
            return parsed
        entries = leadership_payload.get("leadership_changes", [])
        return {
            "confirmed": len(entries) > 0,
            "rationale": "fallback based on explicit leadership change list",
            "confidence": 0.66 if entries else 0.5,
        }

    async def booking_summary(self, booking_payload: dict[str, Any]) -> str:
        prompt = (
            "Write a short booking summary for CRM timeline. Return plain text only.\n"
            f"{json.dumps(booking_payload, default=str)}"
        )
        result = await get_openrouter_client().complete(
            task_type="summarization",
            prompt=prompt,
            function_name="booking_summary",
        )
        text = str(result.get("text", "")).strip()
        if text:
            return text
        return "Prospect booked a follow-up call; aligned next step is discovery and signal review."


_LAYER: LLMReasoningLayer | None = None


def get_reasoning_layer() -> LLMReasoningLayer:
    global _LAYER
    if _LAYER is None:
        _LAYER = LLMReasoningLayer()
    return _LAYER
