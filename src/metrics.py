"""
Prometheus Metrics Configuration
Defines custom metrics for tracking application performance and business metrics.
"""

import time

from prometheus_client import Counter, Histogram
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

# HTTP Request Metrics
http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# Business Metrics
articles_processed_total = Counter(
    "articles_processed_total", "Total articles processed", ["source"]
)

sentiment_analysis_total = Counter(
    "sentiment_analysis_total", "Total sentiment analyses", ["sentiment"]
)

embedding_generation_duration_seconds = Histogram(
    "embedding_generation_duration_seconds",
    "Time to generate embeddings",
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
)

bedrock_api_calls_total = Counter(
    "bedrock_api_calls_total",
    "Total Bedrock API calls",
    ["model", "operation", "status"],
)


class MetricsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically track HTTP request metrics.

    Tracks:
    - Total requests by method, endpoint, and status code
    - Request duration/latency by method and endpoint
    """

    async def dispatch(self, request: Request, call_next):
        # Skip metrics endpoint itself to avoid infinite loop
        if request.url.path == "/metrics":
            return await call_next(request)

        # Record start time
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Record metrics
        http_requests_total.labels(
            method=request.method, endpoint=request.url.path, status=response.status_code
        ).inc()

        http_request_duration_seconds.labels(
            method=request.method, endpoint=request.url.path
        ).observe(duration)

        return response

