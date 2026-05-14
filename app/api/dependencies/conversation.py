from fastapi import Request

from app.services.chat.conversation_state import ConversationStateService


async def get_conversation_state(request: Request) -> tuple[str | None, dict]:
    conversation_id = getattr(request.state, "conversation_id", None)

    if not conversation_id:
        return None, {}

    state = await ConversationStateService.get(conversation_id)

    return conversation_id, state
