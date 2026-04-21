from __future__ import annotations

FAILURE_TAXONOMY = {
    "classification": ["icp_false_positive", "icp_false_negative", "abstention_miss"],
    "grounding": ["unsupported_claim", "hallucinated_signal", "stale_source_citation"],
    "tone": ["condescension", "aggressive_sales_tone", "exaggeration"],
    "operations": ["scheduling_error", "crm_sync_error", "sms_fallback_miss"],
    "economics": ["cost_overrun", "token_spike", "retry_storm"],
}
