from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class Severity(str, Enum):
    low = "low"
    medium = "medium"
    high = "high"


class SignalRecord(BaseModel):
    value: Any
    confidence: float = Field(ge=0.0, le=1.0)
    source: str
    timestamp: datetime


class CompanyInput(BaseModel):
    company_id: str
    name: str
    domain: str
    industry: str
    employee_count: int
    founded_year: int
    latest_funding_date: str | None = None
    latest_funding_round: str | None = None
    leadership_changes: list[str] = Field(default_factory=list)
    open_roles: list[str] = Field(default_factory=list)
    layoffs_reported: bool = False
    tech_stack: list[str] = Field(default_factory=list)
    exec_public_mentions: list[str] = Field(default_factory=list)
    github_activity_score: float | None = None


class ScoredCompany(BaseModel):
    company: CompanyInput
    signals: dict[str, SignalRecord]
    ai_maturity_score: int = Field(ge=0, le=3)
    ai_maturity_explanation: str
    icp_segment: Literal["segment_1", "segment_2", "segment_3", "segment_4", "abstain"]
    icp_confidence: float = Field(ge=0.0, le=1.0)
    icp_rationale: str


class OutreachDraft(BaseModel):
    channel: Literal["email", "sms"]
    subject: str | None = None
    body: str
    personalized_signals: list[str] = Field(default_factory=list)


class ValidatorResult(BaseModel):
    accepted: bool
    reasons: list[str] = Field(default_factory=list)


class ConversationOutcome(BaseModel):
    intent: Literal[
        "positive_interest",
        "needs_more_info",
        "not_now",
        "unsubscribe",
        "book_meeting",
        "unknown",
    ]
    route: Literal["email_followup", "sms_followup", "schedule", "human_handoff", "stop"]
    notes: str


class ProbeResult(BaseModel):
    input: str
    expected_failure: str
    observed_behavior: str
    severity: Severity


class BenchResult(BaseModel):
    dataset: str
    pass_at_1: float
    ci_low: float
    ci_high: float
    avg_cost_usd: float


class EngineRunReport(BaseModel):
    mode: Literal["interim", "final"]
    processed_companies: int
    emails_sent: int
    crm_records: int
    bench: BenchResult
    probes: list[ProbeResult] = Field(default_factory=list)
