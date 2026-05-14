import asyncio

from app.evals.answer_eval import run_answer_eval
from app.evals.retrieval_eval import run_retrieval_eval


async def main() -> None:
    print("\nRunning retrieval eval...\n")
    await run_retrieval_eval()

    print("\nRunning answer eval...\n")
    await run_answer_eval()


if __name__ == "__main__":
    asyncio.run(main())
