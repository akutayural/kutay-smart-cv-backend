import re
from functools import lru_cache

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from rank_bm25 import BM25Okapi

from app.core.config import get_settings
from app.core.qdrant import qdrant_client
from app.ai.rag.ingest import load_documents
from app.ai.rag.reranker import rerank_documents
from app.observability import track_event, track_timing
from app.observability.prometheus import (
    EMBEDDING_LATENCY,
    RAG_RETRIEVAL_LATENCY,
    RERANK_LATENCY,
)

INTENT_SOURCE_PRIORITY = {
    "visa": {"visa.md"},
    "availability": {"visa.md", "personal.md"},
    "skills": {"skills.md", "experience.md", "projects.md"},
    "projects": {"projects.md", "achievements.md"},
    "experience": {"experience.md", "projects.md", "achievements.md"},
    "education": {"education.md", "projects.md"},
    "role_fit": {"profile.md", "skills.md", "experience.md", "projects.md", "achievements.md"},
    "professional_background": {"profile.md", "experience.md", "projects.md", "achievements.md"},
    "personal_context": {"personal.md", "profile.md"},
    "hobbies": {"personal.md"},
    "work_style": {"personal.md", "profile.md"},
    "values": {"personal.md", "profile.md"},
}

STRICT_INTENTS = {
    "visa",
    "skills",
    "projects",
    "education",
}


def _filter_candidates_by_intent(
    documents: list[Document],
    intent: str | None,
) -> list[Document]:
    if intent not in STRICT_INTENTS:
        return documents

    preferred_sources = INTENT_SOURCE_PRIORITY.get(intent)

    if not preferred_sources:
        return documents

    filtered = [
        doc
        for doc in documents
        if str(doc.metadata.get("source", "")) in preferred_sources
    ]

    return filtered or documents


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def _doc_key(doc: Document) -> str:
    return "|".join(
        [
            str(doc.metadata.get("source", "")),
            str(doc.metadata.get("section", "")),
            str(doc.metadata.get("subsection", "")),
            str(doc.metadata.get("chunk_index", "")),
            doc.page_content[:80],
        ]
    )


def _apply_intent_boost(
    doc: Document,
    score: float,
    intent: str | None,
) -> float:
    if not intent:
        return score

    preferred_sources = INTENT_SOURCE_PRIORITY.get(intent)

    if not preferred_sources:
        return score

    source = str(doc.metadata.get("source", ""))

    if source in preferred_sources:
        return score * 1.35

    return score * 0.85


@lru_cache(maxsize=1)
def get_embeddings() -> OpenAIEmbeddings:
    settings = get_settings()

    return OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        api_key=settings.openai_api_key,
    )


@lru_cache(maxsize=1)
def get_bm25_index() -> tuple[BM25Okapi, list[Document]]:
    documents = load_documents()

    tokenized_corpus = [
        _tokenize(
            " ".join(
                [
                    doc.page_content,
                    str(doc.metadata.get("source", "")),
                    str(doc.metadata.get("chunk_title", "")),
                    str(doc.metadata.get("section", "")),
                    str(doc.metadata.get("subsection", "")),
                ]
            )
        )
        for doc in documents
    ]

    return BM25Okapi(tokenized_corpus), documents


def _keyword_overlap_score(question: str, doc: Document) -> float:
    query_tokens = set(_tokenize(question))

    doc_tokens = set(
        _tokenize(
            " ".join(
                [
                    doc.page_content,
                    str(doc.metadata.get("source", "")),
                    str(doc.metadata.get("chunk_title", "")),
                    str(doc.metadata.get("section", "")),
                    str(doc.metadata.get("subsection", "")),
                ]
            )
        )
    )

    if not query_tokens:
        return 0.0

    return len(query_tokens & doc_tokens) / len(query_tokens)


def _payload_to_document(payload: dict) -> Document:
    page_content = str(
        payload.get("page_content")
        or payload.get("content")
        or payload.get("text")
        or ""
    )

    metadata = payload.get("metadata") or {}

    if not isinstance(metadata, dict):
        metadata = {}

    return Document(
        page_content=page_content,
        metadata=metadata,
    )


async def retrieve_context_with_scores(
    question: str,
    k: int = 8,
) -> list[tuple[Document, float]]:
    settings = get_settings()
    embeddings = get_embeddings()

    with EMBEDDING_LATENCY.time():
        with track_timing("embedding_query_timing"):
            query_vector = await embeddings.aembed_query(question)

    with track_timing(
            "qdrant_query_timing",
            collection=settings.qdrant_collection,
            limit=k,
    ):
        response = await qdrant_client.query_points(
            collection_name=settings.qdrant_collection,
            query=query_vector,
            limit=k,
            with_payload=True,
        )

    points = response.points if hasattr(response, "points") else response

    return [
        (_payload_to_document(point.payload or {}), point.score or 0.0)
        for point in points
    ]


def bm25_retrieve_context(question: str, k: int = 8) -> list[Document]:
    bm25, documents = get_bm25_index()

    scores = bm25.get_scores(_tokenize(question))

    ranked_indices = sorted(
        range(len(scores)),
        key=lambda index: scores[index],
        reverse=True,
    )

    return [
        documents[index]
        for index in ranked_indices[:k]
        if scores[index] > 0
    ]


async def hybrid_retrieve_context(
    question: str,
    k: int = 5,
    intent: str | None = None,
    vector_k: int = 12,
    bm25_k: int = 12,
) -> list[Document]:
    vector_results = await retrieve_context_with_scores(question, k=vector_k)
    bm25_results = bm25_retrieve_context(question, k=bm25_k)

    fused: dict[str, tuple[Document, float]] = {}

    for rank, (doc, _score) in enumerate(vector_results, start=1):
        key = _doc_key(doc)
        current_score = fused.get(key, (doc, 0.0))[1]
        fused[key] = (doc, current_score + 1 / (60 + rank))

    for rank, doc in enumerate(bm25_results, start=1):
        key = _doc_key(doc)
        current_score = fused.get(key, (doc, 0.0))[1]
        fused[key] = (doc, current_score + 1 / (60 + rank))

    adjusted = []

    for doc, score in fused.values():
        score = _apply_intent_boost(doc, score, intent)
        score += _keyword_overlap_score(question, doc) * 0.03
        adjusted.append((doc, score))

    ranked = sorted(
        adjusted,
        key=lambda item: item[1],
        reverse=True,
    )

    return [doc for doc, _score in ranked[:k]]


async def retrieve_context(
    question: str,
    k: int = 5,
    intent: str | None = None,
) -> list[Document]:
    with RAG_RETRIEVAL_LATENCY.time():
        candidates = await hybrid_retrieve_context(
            question=question,
            k=15,
            intent=intent,
            vector_k=15,
            bm25_k=15,
        )

        candidates = _filter_candidates_by_intent(candidates, intent)

        with RERANK_LATENCY.time():
            with track_timing(
                "rerank_timing",
                candidate_count=len(candidates),
                top_k=k,
            ):
                results = rerank_documents(
                    question=question,
                    documents=candidates,
                    top_k=k,
                )

    track_event(
        "retrieval_pipeline_completed",
        intent=intent,
        candidate_count=len(candidates),
        returned_count=len(results),
        sources=[doc.metadata.get("source", "unknown") for doc in results],
    )

    return results