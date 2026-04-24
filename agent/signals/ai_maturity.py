from __future__ import annotations

from agent.core.state import CompanyInput
from core.cache import get_cache

_AI_LEADERSHIP_TERMS = {
    "chief ai officer", "chief artificial intelligence", "vp ai", "vp of ai",
    "head of ai", "director of ai", "ai lead", "cto", "chief data officer",
}
_AI_FRIENDLY_INDUSTRIES = {
    "fintech", "healthtech", "edtech", "adtech", "insurtech",
    "artificial intelligence", "machine learning", "data analytics",
}


def score_ai_maturity(company: CompanyInput) -> tuple[int, str]:
    cache = get_cache()
    key = cache.make_key("score_ai_maturity", "v2", company.model_dump(mode="json"))
    cached = cache.get(key)
    if cached is not None:
        return int(cached["score"]), str(cached["explanation"])

    # Signal 1: open AI/ML roles (hiring intent)
    ai_roles = sum(1 for role in company.open_roles if "ai" in role.lower() or "ml" in role.lower())

    # Signal 2: exec public statements about AI
    exec_mentions = sum(1 for m in company.exec_public_mentions if "ai" in m.lower())

    # Signal 3: AI platform in tech stack
    ai_platforms = {"openai", "vertex ai", "bedrock", "azure openai", "anthropic", "huggingface", "sagemaker"}
    tech_signal = 1 if any(stack.lower() in ai_platforms for stack in company.tech_stack) else 0

    # Signal 4: GitHub activity (proxy for engineering output)
    github_signal = min(company.github_activity_score or 0.0, 1.0)

    # Signal 5: leadership changes with AI-profile titles
    leadership_ai = 1 if any(
        any(term in change.lower() for term in _AI_LEADERSHIP_TERMS)
        for change in company.leadership_changes
    ) else 0

    # Signal 6: industry vertical with strong AI adoption baseline
    industry_ai = 1 if any(term in company.industry.lower() for term in _AI_FRIENDLY_INDUSTRIES) else 0

    # Silent company: all signals absent → score 0, no further computation
    all_absent = (
        ai_roles == 0 and exec_mentions == 0 and tech_signal == 0
        and github_signal == 0.0 and leadership_ai == 0 and industry_ai == 0
    )
    if all_absent:
        explanation = (
            "insufficient_signals: no AI indicators detected across all 6 signal categories "
            "(open_roles, exec_mentions, tech_stack, github_activity, leadership_changes, industry); "
            "confidence=0.00"
        )
        cache.set(key, {"score": 0, "explanation": explanation})
        return 0, explanation

    # Weighted scoring (weights sum to 1.0)
    weighted = (
        (ai_roles * 0.40)
        + (exec_mentions * 0.25)
        + (tech_signal * 0.12)
        + (github_signal * 0.03)
        + (leadership_ai * 0.12)
        + (industry_ai * 0.08)
    )

    # Confidence: fraction of signal categories with a non-zero reading
    signal_present = [ai_roles > 0, exec_mentions > 0, tech_signal > 0,
                      github_signal > 0.0, leadership_ai > 0, industry_ai > 0]
    confidence = round(sum(signal_present) / len(signal_present), 2)

    if weighted < 0.5:
        score = 0
    elif weighted < 1.5:
        score = 1
    elif weighted < 2.8:
        score = 2
    else:
        score = 3

    explanation = (
        f"AI roles={ai_roles} (w=0.40), exec AI mentions={exec_mentions} (w=0.25), "
        f"tech signal={tech_signal} (w=0.12), github signal={github_signal:.2f} (w=0.03), "
        f"leadership AI={leadership_ai} (w=0.12), industry AI baseline={industry_ai} (w=0.08); "
        f"weighted={weighted:.2f}, score={score}, confidence={confidence}"
    )
    cache.set(key, {"score": score, "explanation": explanation})
    return score, explanation
