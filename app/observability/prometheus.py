from prometheus_client import Counter, Histogram

REQUEST_COUNT = Counter(
    "cv_ai_requests_total",
    "Total API requests",
    ["method", "path"],
)

REQUEST_LATENCY = Histogram(
    "cv_ai_request_latency_seconds",
    "API request latency",
    ["method", "path"],
)

LLM_REQUEST_COUNT = Counter(
    "cv_ai_llm_requests_total",
    "Total LLM requests",
    ["model"],
)

RAG_RETRIEVAL_LATENCY = Histogram(
    "cv_ai_rag_retrieval_latency_seconds",
    "RAG retrieval latency",
)

RERANK_LATENCY = Histogram(
    "cv_ai_rerank_latency_seconds",
    "Rerank latency",
)

EMBEDDING_LATENCY = Histogram(
    "cv_ai_embedding_latency_seconds",
    "Embedding latency",
)
