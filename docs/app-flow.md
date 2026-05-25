# Application Flow

This project is a hybrid search engine that combines:

- PostgreSQL for document governance and metadata
- OpenSearch for BM25 keyword retrieval
- FAISS for dense vector retrieval
- Cohere Rerank for final ranking refinement
- Redis for embedding cache
- MinIO as the source for ingestion datasets

## 1) Startup flow

When the app starts, `main.py` creates the FastAPI application and exposes:

- `GET /` for basic status
- `GET /health` for component health checks
- `POST /search` for querying the system

The `SearchEngine` is loaded through a cached dependency so the model, OpenSearch client, FAISS index, and reranker are reused instead of recreated on every request.

## 2) Document ingestion flow

Document ingestion is handled by `DocumentIngestionService`.

### What it does

For each batch of documents it:

1. Validates that each document has the required fields.
2. Upserts the document into PostgreSQL as the source of truth.
3. Builds embeddings from the title + content.
4. Adds or updates vectors in FAISS.
5. Bulk indexes the same batch into OpenSearch.

### Where the data comes from

There are ingestion pipelines for different sources:

- `ArxivPipeline` reads JSONL documents from MinIO
- `StackOverflowPipeline` reads StackOverflow XML from MinIO

Both pipelines stream documents in batches so the system can ingest large datasets without loading everything into memory.

## 3) Search flow

A search request goes through `SearchEngine.search()`.

### Step-by-step

1. The API validates the query and `top_k`.
2. The hybrid search service runs lexical and dense retrieval.
3. BM25 search happens through OpenSearch.
4. Query embeddings are generated and cached in Redis.
5. FAISS searches the dense vector index.
6. Reciprocal Rank Fusion merges both result sets.
7. Cohere reranks the fused candidates.
8. PostgreSQL metadata enriches the results and filters inactive documents.
9. The final ranked list is returned to the API.

## 4) Health flow

`GET /health` checks:

- OpenSearch availability
- embedding model availability
- FAISS readiness
- PostgreSQL metadata connectivity

If any critical component is unhealthy, the API returns `503`.

## 5) Data responsibility by system

### PostgreSQL

Stores document metadata, versioning, and active/inactive status.

### OpenSearch

Stores searchable text for BM25 retrieval.

### FAISS

Stores dense vectors for semantic retrieval.

### Redis

Caches query embeddings to reduce repeated model inference.

### MinIO

Stores the source files used by ingestion pipelines.

## 6) Important design idea

The system is intentionally split into two paths:

- ingestion path: prepares and stores documents in all retrieval layers
- search path: queries those layers, fuses results, reranks them, and enriches them

That separation is what makes the app feel like a production-style hybrid retrieval system instead of a single search script.
