from __future__ import annotations

from agent.core.state import CompanyInput, SignalRecord


def generate_hiring_brief(company: CompanyInput, signals: dict[str, SignalRecord]) -> str:
    lines = [f"Hiring signal brief for {company.name}:"]
    for key in ("job_velocity", "leadership_change", "layoffs", "tech_stack_match"):
        sig = signals[key]
        lines.append(
            f"- {key}: value={sig.value}, confidence={sig.confidence:.2f}, source={sig.source}, "
            f"timestamp={sig.timestamp.isoformat()}"
        )

    tone = "high-confidence" if signals["job_velocity"].confidence >= 0.8 else "moderate-confidence"
    lines.append(f"Narrative: {company.name} shows {tone} hiring dynamics based on structured sources above.")
    return "\n".join(lines)
