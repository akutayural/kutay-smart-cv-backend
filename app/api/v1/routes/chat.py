from app.api.dependencies.conversation import get_conversation_state
from app.core.logging import get_logger
from fastapi import APIRouter, Depends, Request

from app.core.rate_limit import limiter
from app.schemas.chat import ChatRequest
from fastapi.responses import StreamingResponse

from app.services.chat.chat import stream_chat_as_sse

logger = get_logger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/stream")
@limiter.limit("10/minute")
async def chat_stream(
        request: Request,
        body: ChatRequest,
        conversation: tuple[str | None, dict] = Depends(get_conversation_state),
):
    """
    Streaming chat endpoint using Server-Sent Events (SSE).
    Tokens are streamed incrementally to the client to reduce perceived
    latency and improve conversational UX.
    """
    conversation_id, state = conversation

    logger.info(
        "stream_chat_request_received",
        message_length=len(body.message),
        conversation_id=conversation_id,
    )

    return StreamingResponse(
        stream_chat_as_sse(body.message,
                           conversation_id=conversation_id,
                           conversation_state=state),
        media_type="text/event-stream",
        headers={
            # Disable proxy buffering so tokens flush immediately.
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
