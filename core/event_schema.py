from __future__ import annotations

from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ErrorCode(str, Enum):
    warm_lead_guard_block = "warm_lead_guard_block"
    missing_message = "missing_message"
    malformed_webhook = "malformed_webhook"
    send_failure = "send_failure"
    bounce_event = "bounce_event"
    unsupported_event = "unsupported_event"


class LeadContext(BaseModel):
    prospect_id: str
    email: str | None = None
    prior_email_engagement: bool = False
    enrichment_fields: dict[str, Any] = Field(default_factory=dict)


class ChannelEvent(BaseModel):
    channel: Literal["email", "sms"]
    event_type: str
    prospect_id: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)


class ChannelError(BaseModel):
    channel: Literal["email", "sms"]
    code: ErrorCode
    detail: str
    payload: dict[str, Any] = Field(default_factory=dict)

