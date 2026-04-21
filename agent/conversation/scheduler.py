from __future__ import annotations


def should_schedule(reply_text: str) -> bool:
    text = reply_text.lower()
    schedule_tokens = ["tuesday", "wednesday", "thursday", "friday", "10am", "2pm", "calendar"]
    return any(token in text for token in schedule_tokens)
