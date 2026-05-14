import json

from app.evals.datasets.answer_evalset import ANSWER_EVALSET
from app.services.chat.chat import stream_chat_as_sse


async def collect_sse_answer(question: str) -> str:
    answer = ""

    async for raw_event in stream_chat_as_sse(
        question=question,
        conversation_id=None,
        conversation_state=None,
    ):
        if not raw_event.startswith("data:"):
            continue

        payload = raw_event.removeprefix("data:").strip()

        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            continue

        event_type = event.get("type")
        content = event.get("content") or ""

        if event_type in {"token", "final"}:
            answer += content

        if event_type == "replace":
            return content

    return answer.strip()


def contains_expected_groups(
    answer: str,
    expected_any_groups: list[list[str]],
) -> bool:
    lower = answer.lower()

    return all(
        any(keyword.lower() in lower for keyword in group)
        for group in expected_any_groups
    )


def contains_no_forbidden_keywords(
    answer: str,
    forbidden: list[str],
) -> bool:
    lower = answer.lower()

    return not any(keyword.lower() in lower for keyword in forbidden)


async def run_answer_eval() -> None:
    passed = 0

    for item in ANSWER_EVALSET:
        answer = await collect_sse_answer(item["question"])

        keyword_pass = contains_expected_groups(
            answer,
            item["expected_any_groups"],
        )

        forbidden_pass = contains_no_forbidden_keywords(
            answer,
            item["forbidden_keywords"],
        )

        ok = keyword_pass and forbidden_pass
        passed += int(ok)

        print("=" * 80)
        print("QUESTION:", item["question"])
        print("ANSWER:", answer[:700])
        print("keyword_pass:", keyword_pass)
        print("forbidden_pass:", forbidden_pass)
        print("pass:", ok)

    print("\nFINAL ANSWER EVAL")
    print("Pass Rate:", passed / len(ANSWER_EVALSET))
