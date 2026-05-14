import pytest

from app.ai.guardrails.scope import understand_message
from app.ai.rag.retriever import retrieve_context


def assert_any_source(docs, source: str):
    assert any(doc.metadata.get("source") == source for doc in docs)


@pytest.mark.asyncio
async def test_retrieves_visa_context():
    query = "Does Kutay require visa sponsorship?"

    understanding = understand_message(query)

    docs = await retrieve_context(
        query,
        k=5,
        intent=understanding["intent"],
    )

    assert_any_source(docs, "visa.md")


@pytest.mark.asyncio
async def test_retrieves_skills_context():
    query = "What is Kutay's strongest backend stack?"

    understanding = understand_message(query)

    docs = await retrieve_context(
        query,
        k=5,
        intent=understanding["intent"],
    )

    assert_any_source(docs, "skills.md")


@pytest.mark.asyncio
async def test_retrieves_open_source_context():
    query = "What open source work has Kutay done?"

    understanding = understand_message(query)

    docs = await retrieve_context(
        query,
        k=5,
        intent=understanding["intent"],
    )

    assert any(
        "APIException" in (doc.metadata.get("chunk_title") or "")
        or "APIException" in doc.page_content
        for doc in docs
    )


@pytest.mark.asyncio
async def test_retrieves_fraud_detection_context():
    query = "Has Kutay built fraud detection systems?"

    understanding = understand_message(query)

    docs = await retrieve_context(
        query,
        k=5,
        intent=understanding["intent"],
    )

    assert any(
        "Limbo Fraud Detection System" in (doc.metadata.get("chunk_title") or "")
        or "fraud" in doc.page_content.lower()
        for doc in docs
    )
