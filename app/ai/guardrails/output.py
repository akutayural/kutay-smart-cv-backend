import re

FALLBACK_ANSWER = (
    "I do not have enough information in Kutay's Smart CV knowledge base to answer that."
)

_LEAKAGE_PATTERNS = [
    re.compile(r"system\s+prompt", re.IGNORECASE),
    re.compile(r"developer\s+message", re.IGNORECASE),
    re.compile(r"hidden\s+instructions?", re.IGNORECASE),
    re.compile(r"api[\s_-]?key", re.IGNORECASE),
    re.compile(r"bearer\s+token", re.IGNORECASE),
    re.compile(r"\.env", re.IGNORECASE),
]


def validate_output(answer: str | None) -> str:
    if not answer or not answer.strip():
        return FALLBACK_ANSWER

    cleaned = answer.strip()

    if any(pattern.search(cleaned) for pattern in _LEAKAGE_PATTERNS):
        return FALLBACK_ANSWER

    return cleaned
