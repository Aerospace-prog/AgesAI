"""Prometheus metrics for AgesAI services.

Defines standard application metrics using the prometheus_client library.
Metrics are exposed via a /metrics endpoint in each FastAPI service.
"""

from prometheus_client import Counter, Histogram, Gauge, Info


# ── Request Metrics ──

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    labelnames=["method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    labelnames=["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# ── Service-Specific Metrics ──

EMBEDDING_JOBS_TOTAL = Counter(
    "embedding_jobs_total",
    "Total number of embedding jobs",
    labelnames=["status"],  # started, completed, failed
)

EMBEDDING_CHUNKS_PROCESSED = Counter(
    "embedding_chunks_processed_total",
    "Total number of code chunks embedded",
)

SEARCH_QUERIES_TOTAL = Counter(
    "search_queries_total",
    "Total number of search queries",
    labelnames=["search_type"],  # semantic, hybrid
)

SEARCH_LATENCY = Histogram(
    "search_latency_seconds",
    "Search query latency in seconds",
    labelnames=["search_type"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5),
)

LLM_REQUESTS_TOTAL = Counter(
    "llm_requests_total",
    "Total number of LLM API requests",
    labelnames=["model", "status"],
)

LLM_TOKEN_USAGE = Counter(
    "llm_token_usage_total",
    "Total tokens consumed by LLM calls",
    labelnames=["model", "direction"],  # direction: input, output
)

LLM_REQUEST_DURATION = Histogram(
    "llm_request_duration_seconds",
    "LLM API request duration in seconds",
    labelnames=["model"],
    buckets=(0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0),
)

# ── Infrastructure Metrics ──

ACTIVE_CONNECTIONS = Gauge(
    "active_connections",
    "Number of active connections",
    labelnames=["service"],  # postgres, redis, qdrant, kafka
)

SERVICE_INFO = Info(
    "service",
    "Service metadata",
)
