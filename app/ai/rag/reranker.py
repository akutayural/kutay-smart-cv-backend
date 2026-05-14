import json

from langchain_core.documents import Document
from openai import OpenAI

from app.core.config import get_settings


RERANKER_SYSTEM_PROMPT = """
You are a strict retrieval reranker for Ahmet Kutay Ural's Smart CV assistant.

Rank the provided chunks by how useful they are for answering the user question.

Rules:
- Prefer chunks that directly answer the question.
- Prefer specific evidence over broad profile summaries.
- Prefer project, experience, skills, visa, or achievement chunks when they directly match.
- Do not invent information.
- Return ONLY valid JSON.

JSON shape:
{
  "ranked_ids": [0, 2, 1]
}
"""


def _format_candidate(index: int, doc: Document) -> str:
    return "\n".join(
        [
            f"ID: {index}",
            f"Source: {doc.metadata.get('source')}",
            f"Title: {doc.metadata.get('chunk_title')}",
            f"Section: {doc.metadata.get('section')}",
            f"Subsection: {doc.metadata.get('subsection')}",
            "Content:",
            doc.page_content[:1200],
        ]
    )


def rerank_documents(
    question: str,
    documents: list[Document],
    top_k: int = 5,
) -> list[Document]:
    if len(documents) <= top_k:
        return documents

    settings = get_settings()
    client = OpenAI(api_key=settings.openai_api_key)

    candidates = "\n\n---\n\n".join(
        _format_candidate(index, doc)
        for index, doc in enumerate(documents)
    )

    response = client.chat.completions.create(
        model=settings.scope_classifier_model,
        messages=[
            {"role": "system", "content": RERANKER_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": (
                    f"Question:\n{question}\n\n"
                    f"Candidate chunks:\n{candidates}"
                ),
            },
        ],
        temperature=0,
        max_tokens=200,
        response_format={"type": "json_object"},
    )

    raw = response.choices[0].message.content or "{}"

    try:
        payload = json.loads(raw)
        ranked_ids = payload.get("ranked_ids", [])
    except Exception:
        return documents[:top_k]

    selected: list[Document] = []
    seen: set[int] = set()

    for item in ranked_ids:
        if not isinstance(item, int):
            continue

        if item < 0 or item >= len(documents):
            continue

        if item in seen:
            continue

        selected.append(documents[item])
        seen.add(item)

        if len(selected) >= top_k:
            break

    if len(selected) < top_k:
        for index, doc in enumerate(documents):
            if index in seen:
                continue

            selected.append(doc)

            if len(selected) >= top_k:
                break

    return selected
