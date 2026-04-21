from __future__ import annotations

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


class Paths(BaseModel):
    base_dir: Path = Field(default_factory=lambda: Path(__file__).resolve().parents[2])

    @property
    def data_dir(self) -> Path:
        return self.base_dir / "data"

    @property
    def config_path(self) -> Path:
        return self.base_dir / "config" / "settings.yaml"
