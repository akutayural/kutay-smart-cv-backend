import asyncio

from app.ai.rag.retriever import retrieve_context
from app.evals.datasets.retrieval_evalset import RETRIEVAL_EVALSET
from app.evals.metrics import hit_rate, reciprocal_rank


async def run_retrieval_eval():
    total_hits = 0
    total_mrr = 0.0

    for item in RETRIEVAL_EVALSET:
        docs = await retrieve_context(
            question=item["question"],
            intent=item["intent"],
            k=5,
        )

        sources = [
            doc.metadata.get("source")
            for doc in docs
        ]

        hit = hit_rate(
            sources,
            item["expected_sources"],
        )

        rr = reciprocal_rank(
            sources,
            item["expected_sources"],
        )

        total_hits += int(hit)
        total_mrr += rr

        print("=" * 80)
        print(item["question"])
        print("sources:", sources)
        print("hit:", hit)
        print("mrr:", rr)

    print("\nFINAL RESULTS")
    print("Hit Rate:", total_hits / len(RETRIEVAL_EVALSET))
    print("MRR:", total_mrr / len(RETRIEVAL_EVALSET))


if __name__ == "__main__":
    asyncio.run(run_retrieval_eval())