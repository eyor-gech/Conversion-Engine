from __future__ import annotations

from agent.core.state import CompanyInput


def score_ai_maturity(company: CompanyInput) -> tuple[int, str]:
    ai_roles = sum(1 for role in company.open_roles if "ai" in role.lower() or "ml" in role.lower())
    exec_mentions = sum(1 for m in company.exec_public_mentions if "ai" in m.lower())
    tech_signal = 1 if any(stack.lower() in {"openai", "vertex ai", "bedrock"} for stack in company.tech_stack) else 0
    github_signal = company.github_activity_score or 0.0

    weighted = (ai_roles * 0.5) + (exec_mentions * 0.3) + (tech_signal * 0.15) + (github_signal * 0.05)

    if weighted < 0.5:
        score = 0
    elif weighted < 1.5:
        score = 1
    elif weighted < 2.8:
        score = 2
    else:
        score = 3

    explanation = (
        f"AI roles={ai_roles}, exec AI mentions={exec_mentions}, "
        f"tech signal={tech_signal}, github signal={github_signal:.2f}, weighted={weighted:.2f}"
    )
    return score, explanation
