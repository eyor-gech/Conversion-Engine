from __future__ import annotations

from typing import Literal


def classify_intent(reply_text: str) -> Literal[
    "positive_interest",
    "needs_more_info",
    "not_now",
    "unsubscribe",
    "book_meeting",
    "unknown",
]:
    text = reply_text.lower()
    if any(k in text for k in ["unsubscribe", "stop", "remove me"]):
        return "unsubscribe"
    if any(k in text for k in ["book", "calendar", "meeting", "slot"]):
        return "book_meeting"
    if any(k in text for k in ["interested", "sounds good", "let's talk"]):
        return "positive_interest"
    if any(k in text for k in ["send details", "more info", "case study"]):
        return "needs_more_info"
    if any(k in text for k in ["later", "next quarter", "not now"]):
        return "not_now"
    return "unknown"
