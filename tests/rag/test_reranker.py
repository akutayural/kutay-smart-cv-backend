from app.ai.rag.reranker import rerank_documents
from app.ai.rag.ingest import load_documents
import pytest


@pytest.mark.integration
def test_reranker_prioritizes_apiexception():
    documents = load_documents()

    candidates = [
        doc for doc in documents
        if doc.metadata.get("source") in {"projects.md", "achievements.md", "profile.md"}
    ][:12]

    ranked = rerank_documents(
        question="What open source work has Kutay done?",
        documents=candidates,
        top_k=5,
    )

    assert any(
        "APIException" in (doc.metadata.get("chunk_title") or "")
        or "APIException" in doc.page_content
        for doc in ranked[:2]
    )
