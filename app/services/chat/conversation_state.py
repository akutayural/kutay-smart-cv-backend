import json
from typing import Any

from app.core.config import get_settings
from app.core.redis import redis_client

settings = get_settings()


class ConversationStateService:
    @staticmethod
    def _key(conversation_id: str) -> str:
        return f"conversation:{conversation_id}"

    @staticmethod
    async def get(conversation_id: str) -> dict[str, Any]:
        raw = await redis_client.get(ConversationStateService._key(conversation_id))

        if not raw:
            return {}

        return json.loads(raw)

    @staticmethod
    async def set(conversation_id: str, state: dict[str, Any]) -> None:
        await redis_client.set(
            ConversationStateService._key(conversation_id),
            json.dumps(state),
            ex=settings.conversation_ttl_seconds,
        )

