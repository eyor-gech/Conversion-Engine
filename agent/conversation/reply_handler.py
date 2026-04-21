from __future__ import annotations

from agent.conversation.intent_classifier import classify_intent
from agent.conversation.scheduler import should_schedule
from agent.core.state import ConversationOutcome


def handle_reply(reply_text: str) -> ConversationOutcome:
    intent = classify_intent(reply_text)

    if intent == "unsubscribe":
        return ConversationOutcome(intent=intent, route="stop", notes="Do-not-contact applied")
    if intent == "book_meeting" or should_schedule(reply_text):
        return ConversationOutcome(intent=intent, route="schedule", notes="Trigger Cal.com booking flow")
    if intent == "positive_interest":
        return ConversationOutcome(intent=intent, route="sms_followup", notes="Warm lead fallback to SMS")
    if intent == "not_now":
        return ConversationOutcome(intent=intent, route="email_followup", notes="Send delayed follow-up")
    if intent == "needs_more_info":
        return ConversationOutcome(intent=intent, route="human_handoff", notes="Assign SDR for detailed response")

    return ConversationOutcome(intent="unknown", route="email_followup", notes="Default clarification follow-up")
