from app.ai.rag.ingest import load_documents


def test_load_documents_returns_chunks():
    documents = load_documents()

    assert documents
    assert len(documents) > 20


def test_documents_have_required_metadata():
    documents = load_documents()

    for doc in documents:
        assert doc.page_content
        assert doc.metadata.get("source")
        assert doc.metadata.get("chunk_title") or doc.metadata.get("section")


def test_no_duplicate_chunks():
    documents = load_documents()

    contents = [
        " ".join(doc.page_content.lower().split())
        for doc in documents
    ]

    assert len(contents) == len(set(contents))