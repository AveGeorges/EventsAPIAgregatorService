from prometheus_client import Counter, Gauge, Histogram

HISTOGRAM_BUCKETS = (0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0)

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "endpoint", "status"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
    buckets=HISTOGRAM_BUCKETS,
)

EVENTS_PROVIDER_REQUESTS_TOTAL = Counter(
    "events_provider_requests_total",
    "Total number of requests to Events Provider API",
    ["endpoint", "status"],
)

EVENTS_PROVIDER_REQUEST_DURATION_SECONDS = Histogram(
    "events_provider_request_duration_seconds",
    "Events Provider API request duration in seconds",
    ["endpoint"],
    buckets=HISTOGRAM_BUCKETS,
)

TICKETS_CREATED_TOTAL = Gauge(
    "tickets_created_total",
    "Total number of tickets in database",
)

TICKETS_CANCELLED_TOTAL = Gauge(
    "tickets_cancelled_total",
    "Total number of cancelled tickets in database",
)

EVENTS_TOTAL = Gauge(
    "events_total",
    "Total number of events in database",
)

CACHE_HITS_TOTAL = Counter(
    "cache_hits_total",
    "Total number of cache hits for seats",
)

CACHE_MISSES_TOTAL = Counter(
    "cache_misses_total",
    "Total number of cache misses for seats",
)
