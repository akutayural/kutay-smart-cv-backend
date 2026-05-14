import asyncio

from app.ai.guardrails.scope import understand_message_async
from app.ai.rag.retriever import retrieve_context


QUERIES = [
    "Does Kutay require visa sponsorship?",
    "Has Kutay built fraud detection systems?",
    "What is Kutay's strongest backend stack?",
    "Has Kutay worked with Kubernetes?",
    "Does Kutay have Applied AI experience?",
    "Has Kutay worked on payment systems?",
    "What open source work has Kutay done?",
]


async def main() -> None:
    for query in QUERIES:
        understanding = await understand_message_async(query)
        intent = understanding["intent"]

        print("\n" + "=" * 100)
        print(f"QUERY: {query}")
        print(f"INTENT: {intent}")
        print(f"ALLOWED: {understanding['allowed']}")
        print("=" * 100)

        docs = await retrieve_context(query, k=5, intent=intent)

        for index, doc in enumerate(docs, start=1):
            print(f"\n[{index}]")
            print("source:", doc.metadata.get("source"))
            print("chunk_title:", doc.metadata.get("chunk_title"))
            print("section:", doc.metadata.get("section"))
            print("subsection:", doc.metadata.get("subsection"))
            print(doc.page_content[:500])


if __name__ == "__main__":
    asyncio.run(main())
