from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


class AppSettings(BaseModel):
    app_name: str = "Conversion Engine"
    submission_mode: Literal["interim", "final"] = "interim"
    icp_threshold: float = 0.62
    outreach_tone: str = "consultative"
    hubspot_sandbox: bool = True
    calcom_sandbox: bool = True
    africastalking_sandbox: bool = True
    resend_sandbox: bool = True
    langfuse_enabled: bool = True
    langfuse_project: str = "conversion-engine"
    mock_mode: bool = True
    openrouter_api_key: str = ""
    max_llm_concurrency: int = 2
    max_tool_concurrency: int = 4


class Paths(BaseModel):
    base_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2])

    @property
    def data_dir(self) -> Path:
        return self.base_dir / "data"

    @property
    def config_path(self) -> Path:
        return self.base_dir / "config" / "settings.yaml"


def apply_env_overrides(settings: AppSettings) -> AppSettings:
    payload = settings.model_dump()
    if os.getenv("MOCK_MODE") is not None:
        payload["mock_mode"] = os.getenv("MOCK_MODE", "true").lower() == "true"
    if os.getenv("OPENROUTER_API_KEY") is not None:
        payload["openrouter_api_key"] = os.getenv("OPENROUTER_API_KEY", "")
    if os.getenv("MAX_LLM_CONCURRENCY") is not None:
        payload["max_llm_concurrency"] = max(1, int(os.getenv("MAX_LLM_CONCURRENCY", "2")))
    if os.getenv("MAX_TOOL_CONCURRENCY") is not None:
        payload["max_tool_concurrency"] = max(1, int(os.getenv("MAX_TOOL_CONCURRENCY", "4")))
    return AppSettings.model_validate(payload)
