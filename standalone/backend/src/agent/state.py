"""Conversation and user-reported flood intake facts."""

from langgraph.graph import MessagesState


class OverallState(MessagesState):
    """Store the conversation and its latest extracted intake record."""

    flood_case: dict
    case_message_id: str
    location_lookup: dict
    location_action: dict | None
    location_action_success: bool


class InputState(MessagesState):
    """Accept messages or a location choice, not caller-supplied lookup results."""

    location_action: dict | None
