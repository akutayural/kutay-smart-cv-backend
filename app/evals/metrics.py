def hit_rate(
        retrieved_sources: list[str],
        expected_sources: list[str],
) -> bool:
    return any(
        source in retrieved_sources
        for source in expected_sources
    )


def reciprocal_rank(
        retrieved_sources: list[str],
        expected_sources: list[str],
) -> float:
    for rank, source in enumerate(retrieved_sources, start=1):
        if source in expected_sources:
            return 1 / rank

    return 0.0
