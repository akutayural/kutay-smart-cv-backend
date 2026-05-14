import time

from langgraph.graph import END, StateGraph

from app.core.config import get_settings
from app.core.exceptions import UpstreamError
from app.core.logging import get_logger
from app.ai.guardrails.input import validate_input
from app.ai.guardrails.scope import understand_message_async
from app.ai.rag.prompts import ANSWER_PROMPT
from app.ai.rag.retriever import retrieve_context
from app.ai.workflows.chat.nodes.calendar_availability import calendar_availability_node
from app.ai.workflows.chat.nodes.calendar_confirmation import calendar_confirmation_node
from app.ai.workflows.chat.nodes.calendar_scheduling import calendar_scheduling_node
from app.ai.workflows.chat.state import ChatState
from app.observability import track_error, track_event, track_timing

logger = get_logger(__name__)


def build_initial_state(question: str) -> ChatState:
    return {
        "question": question,
        "allowed": False,
        "refusal_reason": None,
        "documents": [],
        "answer": "",
        "intent": None,
        "stream_ready": False,
        "conversation_context": None,
        "conversation_memory": None,
        "rewritten_question": None,
        "active_entity": None,
        "active_topic": None,
        "meeting_email": None,
        "meeting_purpose": None,
        "meeting_ready_to_schedule": False,
        "meeting_flow_active": False,
        "meeting_requested_start": None,
        "meeting_requested_end": None,
        "meeting_candidate_slots": [],
        "meeting_selected_slot": None,
    }


async def input_guard_node(state: ChatState) -> ChatState:
    logger.info(
        "stream_input_guard_started",
        question=state["question"][:120],
    )

    try:
        validate_input(state["question"])
    except ValueError as error:
        logger.warning(
            "stream_input_guard_failed",
            reason=str(error),
        )

        return {
            **state,
            "allowed": False,
            "refusal_reason": str(error),
            "intent": "out_of_scope",
            "documents": [],
            "answer": str(error),
            "stream_ready": False,
        }

    return {
        **state,
        "allowed": True,
        "refusal_reason": None,
        "stream_ready": False,
    }


async def understanding_node(state: ChatState) -> ChatState:
    logger.info(
        "conversation_understanding_started",
        question=state["question"][:120],
        active_entity=state.get("active_entity"),
    )

    with track_timing(
            "conversation_understanding_timing",
            active_entity=state.get("active_entity"),
    ):
        result = await understand_message_async(
            state["question"],
            conversation_context=state.get("conversation_context"),
            conversation_memory=state.get("conversation_memory"),
            active_entity=state.get("active_entity"),
        )

    logger.info(
        "conversation_understanding_completed",
        allowed=result["allowed"],
        intent=result["intent"],
        rewritten_question=(result.get("rewritten_question") or "")[:160],
        active_entity=result.get("active_entity"),
    )

    return {
        **state,
        "allowed": result["allowed"],
        "refusal_reason": result.get("reason"),
        "intent": result["intent"],
        "rewritten_question": result.get("rewritten_question"),

        # IMPORTANT:
        # Keep previous active entity if LLM returns null
        "active_entity": (
            result.get("active_entity")
            or state.get("active_entity")
        ),

        "answer": "" if result["allowed"] else result.get("reason"),
        "stream_ready": False,
    }


def route_after_input_guard(state: ChatState) -> str:
    if not state.get("allowed"):
        return "refuse"

    return "understand"


def _has_active_meeting_flow(state: ChatState) -> bool:
    return bool(
        state.get("meeting_flow_active")
        or state.get("meeting_email")
        or state.get("meeting_purpose")
        or state.get("meeting_requested_start")
        or state.get("meeting_requested_end")
        or state.get("meeting_candidate_slots")
        or state.get("meeting_selected_slot")
        or state.get("meeting_ready_to_schedule")
    )


def route_after_understanding(state: ChatState) -> str:
    if not state.get("allowed"):
        return "refuse"

    if state.get("intent") == "meeting_confirmation":
        return "calendar_confirmation"

    if _has_active_meeting_flow(state):
        return "calendar_scheduling"

    if state.get("intent") == "meeting_availability":
        return "calendar_availability"

    if state.get("intent") == "meeting_scheduling":
        return "calendar_scheduling"

    return "retrieve"


def refuse_node(state: ChatState) -> ChatState:
    fallback = (
        "I can only answer questions about Kutay's experience, projects, "
        "skills, education, availability, visa status, role fit, or meeting scheduling."
    )

    reason = state.get("refusal_reason")

    if reason:
        normalized_reason = reason.lower().strip()

        if normalized_reason.startswith(
                (
                        "the question is about",
                        "this question is about",
                        "the user is asking",
                        "user is asking",
                        "request for",
                )
        ):
            reason = fallback

    return {
        **state,
        "documents": [],
        "intent": state.get("intent") or "out_of_scope",
        "answer": reason or fallback,
        "stream_ready": False,
    }


async def retrieve_node(state: ChatState) -> ChatState:
    start = time.perf_counter()
    settings = get_settings()

    retrieval_question = state.get("rewritten_question") or state["question"]

    logger.info(
        "stream_retrieval_started",
        question=state["question"][:120],
        rewritten_question=retrieval_question[:200],
        intent=state.get("intent"),
    )

    try:
        with track_timing(
                "rag_retrieval_timing",
                intent=state.get("intent"),
        ):
            documents = await retrieve_context(
                retrieval_question,
                settings.max_context_chunks,
                state.get("intent"),
            )

        logger.info(
            "stream_retrieval_documents",
            documents=[
                {
                    "source": doc.metadata.get("source"),
                    "chunk_title": doc.metadata.get("chunk_title"),
                    "preview": doc.page_content[:180],
                }
                for doc in documents
            ],
        )

    except Exception as exc:
        logger.exception(
            "stream_retrieval_failed",
            error_type=type(exc).__name__,
        )
        track_error(
            "rag_retrieval_failed_observed",
            exc,
            {
                "intent": state.get("intent"),
                "question_preview": state["question"][:120],
            },
        )
        raise UpstreamError("Failed to retrieve context.") from exc

    elapsed_ms = (time.perf_counter() - start) * 1000

    logger.info(
        "stream_retrieval_completed",
        retrieved_chunks=len(documents),
        elapsed_ms=round(elapsed_ms, 2),
        intent=state.get("intent"),
        sources=[
            doc.metadata.get("source", "unknown")
            for doc in documents
        ],
    )

    return {
        **state,
        "documents": documents,
    }


def route_after_retrieve(state: ChatState) -> str:
    return "answer" if state["documents"] else "no_context"


def no_context_node(state: ChatState) -> ChatState:
    logger.warning(
        "stream_retrieval_no_context",
        question=state["question"][:120],
        rewritten_question=(state.get("rewritten_question") or "")[:160],
    )

    return {
        **state,
        "allowed": False,
        "answer": (
            "I do not have enough information in Kutay's Smart CV knowledge base "
            "to answer that."
        ),
        "stream_ready": False,
    }


def _extract_active_entity_from_documents(
        state: ChatState,
) -> tuple[str | None, str | None]:
    documents = state.get("documents") or []

    if not documents:
        return state.get("active_entity"), state.get("active_topic")

    top_doc = documents[0]

    section = top_doc.metadata.get("section")
    document_type = top_doc.metadata.get("document_type")
    chunk_title = top_doc.metadata.get("chunk_title")

    active_entity = section or state.get("active_entity")
    active_topic = document_type or chunk_title or state.get("active_topic")

    return active_entity, active_topic


def answer_node(state: ChatState) -> ChatState:
    context = "\n\n---\n\n".join(
        doc.page_content
        for doc in state["documents"]
    )

    active_entity, active_topic = _extract_active_entity_from_documents(state)

    answer_question = state.get("rewritten_question") or state["question"]

    prompt = ANSWER_PROMPT.format(
        context=context,
        question=answer_question,
    )

    logger.info(
        "stream_answer_generation_prepared",
        context_length=len(context),
        document_count=len(state["documents"]),
        active_entity=active_entity,
        active_topic=active_topic,
    )

    track_event(
        "answer_prompt_prepared",
        context_length=len(context),
        document_count=len(state["documents"]),
        active_entity=active_entity,
        active_topic=active_topic,
    )

    return {
        **state,
        "context": context,
        "prompt": prompt,
        "answer": "",
        "stream_ready": True,
        "active_entity": active_entity,
        "active_topic": active_topic,
    }


def build_streaming_workflow():
    graph = StateGraph(ChatState)

    graph.add_node("input_guard", input_guard_node)
    graph.add_node("understand", understanding_node)
    graph.add_node("refuse", refuse_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("calendar_availability", calendar_availability_node)
    graph.add_node("calendar_scheduling", calendar_scheduling_node)
    graph.add_node("calendar_confirmation", calendar_confirmation_node)
    graph.add_node("no_context", no_context_node)
    graph.add_node("answer", answer_node)

    graph.set_entry_point("input_guard")

    graph.add_conditional_edges(
        "input_guard",
        route_after_input_guard,
        {
            "understand": "understand",
            "refuse": "refuse",
        },
    )

    graph.add_conditional_edges(
        "understand",
        route_after_understanding,
        {
            "retrieve": "retrieve",
            "refuse": "refuse",
            "calendar_availability": "calendar_availability",
            "calendar_scheduling": "calendar_scheduling",
            "calendar_confirmation": "calendar_confirmation",
        },
    )

    graph.add_conditional_edges(
        "retrieve",
        route_after_retrieve,
        {
            "answer": "answer",
            "no_context": "no_context",
        },
    )

    graph.add_edge("calendar_availability", END)
    graph.add_edge("calendar_scheduling", END)
    graph.add_edge("calendar_confirmation", END)
    graph.add_edge("refuse", END)
    graph.add_edge("no_context", END)
    graph.add_edge("answer", END)

    return graph.compile()


streaming_workflow = build_streaming_workflow()
