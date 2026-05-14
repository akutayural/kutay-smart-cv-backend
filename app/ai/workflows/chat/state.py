from typing import NotRequired, TypedDict

from langchain_core.documents import Document


class ChatState(TypedDict):
    question: str
    allowed: bool
    refusal_reason: str | None
    documents: list[Document]
    answer: str
    intent: str | None
    stream_ready: bool

    context: NotRequired[str]
    prompt: NotRequired[str]

    conversation_context: NotRequired[str | None]
    conversation_memory: NotRequired[str | None]
    rewritten_question: NotRequired[str | None]
    active_entity: NotRequired[str | None]
    active_topic: NotRequired[str | None]

    meeting_email: NotRequired[str | None]
    meeting_purpose: NotRequired[str | None]
    meeting_ready_to_schedule: NotRequired[bool]
    meeting_flow_active: NotRequired[bool]

    meeting_requested_start: NotRequired[str | None]
    meeting_requested_end: NotRequired[str | None]

    meeting_candidate_slots: NotRequired[list[dict]]
    meeting_selected_slot: NotRequired[dict | None]
    meeting_flow_decision: NotRequired[str | None]
    