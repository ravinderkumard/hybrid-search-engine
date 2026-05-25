from prometheus_client import Histogram
from prometheus_client import Counter

bm25_latency = Histogram(
    "bm25_latency_seconds",
    "Latency for BM25 OpenSearch queries"
)

embedding_latency = Histogram(
    "embedding_latency_seconds",
    "Latency for query embedding generation"
)

faiss_latency = Histogram(
    "faiss_latency_seconds",
    "Latency for FAISS dense retrieval"
)

rrf_latency = Histogram(
    "rrf_latency_seconds",
    "Latency for RRF fusion"
)

metadata_latency = Histogram(
    "metadata_latency_seconds",
    "Latency for PostgreSQL metadata enrichment"
)

total_search_latency = Histogram(
    "total_search_latency_seconds",
    "End-to-end search pipeline latency"
)

search_errors = Counter(
    "search_errors_total",
    "Total number of failed search requests"
)

search_success = Counter(
    "search_success_total",
    "Total number of successful search requests"
)

search_requests = Counter(
    "search_requests_total",
    "Total number of search requests received"
)

search_validation_errors = Counter(
    "search_validation_errors_total",
    "Total number of invalid search requests"
)

query_length_histogram = Histogram(
    "search_query_length",
    "Length of incoming search queries"
)

top_k_histogram = Histogram(
    "search_top_k_requested",
    "Requested top_k values for search"
)

results_count_histogram = Histogram(
    "search_results_returned",
    "Number of results returned by search queries"
)

hybrid_mode_counter = Counter(
    "hybrid_mode_total",
    "Number of times each hybrid retrieval mode is used",
    ["mode"],
)

dense_confident_counter = Counter(
    "dense_confident_total",
    "Number of searches where dense retrieval was confident"
)

bm25_confident_counter = Counter(
    "bm25_confident_total",
    "Number of searches where BM25 retrieval was confident"
)

dense_only_fallback_counter = Counter(
    "dense_only_fallback_total",
    "Number of times dense-only fallback was used"
)

bm25_only_fallback_counter = Counter(
    "bm25_only_fallback_total",
    "Number of times BM25-only fallback was used"
)

no_strong_match_counter = Counter(
    "no_strong_match_total",
    "Number of searches where neither dense nor BM25 was confident"
)

reranker_success_counter = Counter(
    "reranker_success_total",
    "Number of searches successfully reranked by Cohere"
)

reranker_failed_counter = Counter(
    "reranker_failed_total",
    "Number of searches where reranking failed"
)

reranker_skipped_counter = Counter(
    "reranker_skipped_total",
    "Number of searches where reranking was skipped"
)
